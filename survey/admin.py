import csv
from itertools import groupby

from django.contrib import admin
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django_object_actions import (DjangoObjectActions,
                                   takes_instance_or_queryset)
from reversion.admin import VersionAdmin

from .models import (Answer, Category, Hospital, NationalHealtFund,
                     Participant, Question, Subquestion, Survey)


class ParticipantInline(admin.TabularInline):
    '''
        Tabular Inline View for Participant
    '''
    model = Participant


class HospitalAdmin(VersionAdmin):
    '''
        Admin View for Hospital
    '''
    list_display = ('name', 'email', 'health_fund', 'identifier', 'created', 'modified')
    search_fields = ('name', 'email', 'identifier')


admin.site.register(Hospital, HospitalAdmin)


class HospitalInline(admin.TabularInline):
    '''
        Tabular Inline View for Hospital
    '''
    model = Hospital


class NationalHealtFundAdmin(VersionAdmin):
    '''
        Admin View for NationalHealtFund
    '''
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [
        HospitalInline,
        ParticipantInline,
    ]


admin.site.register(NationalHealtFund, NationalHealtFundAdmin)


class CategoryInline(admin.TabularInline):
    '''
        Tabular Inline View for Category
    '''
    model = Category


class SurveyAdmin(DjangoObjectActions, VersionAdmin):
    '''
        Admin View for Survey
    '''
    actions = ['validate']
    change_actions = ['validate', 'export']
    list_display = ('title', 'created', 'modified', 'is_valid')
    inlines = [
        CategoryInline,
        ParticipantInline,
    ]
    search_fields = ('title', 'welcome_text', 'end_text', 'submit_text')

    def is_valid(self, obj):
        return all(x.status is not False for x in obj.perform_audit())
    is_valid.boolean = True
    is_valid.short_description = _("Is valid?")

    def get_queryset(self, *args, **kwargs):
        qs = super(SurveyAdmin, self).get_queryset(*args, **kwargs)
        return qs.prefetch_full_content().prefetch_related('participants')

    @takes_instance_or_queryset
    def validate(self, request, queryset):
        context = {}
        context['opts'] = self.opts
        context['original'] = context['title'] = ", ".join(map(str, queryset))
        context['has_change_permission'] = request.user.has_perm('survey.change_survey')
        log = []
        for survey in queryset:
            log.extend(survey.perform_audit())
        context['log'] = log
        return render(request, 'survey/survey_admin_validate.html', context=context)
    validate.short_description = _("Validate in detail")
    validate.label = _("Validate")

    def export(self, request, obj):
        response = HttpResponse(content_type='text/csv')
        filename = "export-%s.csv" % (str(obj), )
        response['Content-Disposition'] = 'attachment; filename="%s"' % (filename, )

        def get_key(subquestion):
            return "{title}:{pk}".format(title=subquestion.name, pk=subquestion.pk)

        fieldnames = ['Health fund', 'Hospital']
        fieldnames += [get_key(subquestion) for subquestion in Subquestion.objects.
                       filter(question__category__survey=obj).all()]

        answer_qs = Answer.objects.filter(participant__survey=obj).all()
        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()

        def key(x):
            return (x.participant.health_fund, x.hospital)

        for (participant, hospital), g in groupby(answer_qs, key):
            row = {'Health fund': participant, 'Hospital': hospital}
            row.update({get_key(answer.subquestion): answer.answer for answer in g})
            writer.writerow(row)
        return response


admin.site.register(Survey, SurveyAdmin)


class ParticipantAdmin(VersionAdmin):
    '''
        Admin View for Participant
    '''

    def get_url(self, obj):
        return 'http://%s%s' % (Site.objects.get_current().domain, obj.get_absolute_url())
    list_display = ('pk', 'survey', 'health_fund', 'password', 'get_url')
    list_filter = ('survey', 'health_fund')


admin.site.register(Participant, ParticipantAdmin)


class QuestionInline(admin.TabularInline):
    '''
        Tabular Inline View for Question
    '''
    model = Question


class CategoryAdmin(VersionAdmin):
    '''
        Admin View for Category
    '''
    list_display = ('name', 'survey')
    list_filter = ('survey',)
    search_fields = ('name',)
    inlines = [
        QuestionInline
    ]


admin.site.register(Category, CategoryAdmin)


class SubquestionInline(admin.TabularInline):
    '''
        Tabular Inline View for Subquestion
    '''
    model = Subquestion


class QuestionAdmin(VersionAdmin):
    '''
        Admin View for Question
    '''
    list_display = ('name', 'created', 'modified')
    list_filter = ('category__survey',)
    inlines = [
        SubquestionInline,
    ]
    search_fields = ('name',)


admin.site.register(Question, QuestionAdmin)


class AnswerInline(admin.TabularInline):
    '''
        Stacked Inline View for Answer
    '''
    model = Answer


class SubquestionAdmin(VersionAdmin):
    '''
        Admin View for Subquestion
    '''
    list_display = ('name', 'question', 'kind')
    list_filter = ('question__category__survey',)
    inlines = [
        AnswerInline,
    ]


admin.site.register(Subquestion, SubquestionAdmin)


class AnswerAdmin(VersionAdmin):
    '''
        Admin View for Answer
    '''
    list_display = ('answer', 'participant', 'subquestion', 'hospital')
    list_filter = ('participant', 'subquestion', 'hospital',)


admin.site.register(Answer, AnswerAdmin)
