import csv
from itertools import groupby

from django.contrib import admin, messages
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from django_object_actions import DjangoObjectActions
from import_export.admin import ImportExportMixin
from reversion.admin import VersionAdmin

from .models import (Answer, Category, Hospital, NationalHealtFund,
                     Participant, Question, Subquestion, Survey)
from .resources import (HospitalResource, NationalHealthFundResource,
                        ParticipantResource)


class ParticipantInline(admin.TabularInline):
    '''
        Tabular Inline View for Participant
    '''
    model = Participant


class HospitalAdmin(ImportExportMixin, VersionAdmin):
    '''
        Admin View for Hospital
    '''
    resource_class = HospitalResource
    list_display = ('name', 'email', 'health_fund', 'identifier', 'voivodeship', 'city',
                    'created', 'modified')
    search_fields = ('name', 'email', 'identifier')
    list_filter = ('voivodeship', )


admin.site.register(Hospital, HospitalAdmin)


class HospitalInline(admin.TabularInline):
    '''
        Tabular Inline View for Hospital
    '''
    model = Hospital


class NationalHealtFundAdmin(ImportExportMixin, VersionAdmin):
    '''
        Admin View for NationalHealtFund
    '''
    inlines = [
        HospitalInline,
        ParticipantInline,
    ]
    resource_class = NationalHealthFundResource
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
    change_actions = ['validate', 'export', 'overview', 'stats']
    list_display = ('title', 'created', 'modified', 'is_valid', 'get_style_display')
    inlines = [
        CategoryInline,
        ParticipantInline,
    ]
    search_fields = ('title', 'welcome_text', 'end_text', 'submit_text')
    actions = ['update_subquestion_count', ]

    def is_valid(self, obj):
        return all(x.status is not False for x in obj.perform_audit())
    is_valid.boolean = True
    is_valid.short_description = _("Is valid?")

    def get_queryset(self, *args, **kwargs):
        qs = super(SurveyAdmin, self).get_queryset(*args, **kwargs)
        return qs.prefetch_full_content().prefetch_related('participants')

    def validate(self, request, obj):
        context = {}
        context['opts'] = self.opts
        context['original'] = obj
        context['title'] = self.validate.short_description
        context['has_change_permission'] = request.user.has_perm('survey.change_survey')
        context['object'] = obj
        context['log'] = obj.perform_audit()
        return render(request, 'survey/survey_admin_validate.html', context=context)
    validate.short_description = _("Validate in detail")
    validate.label = _("Validate")

    def overview(self, request, obj):
        context = {}
        context['opts'] = self.opts
        context['original'] = obj
        context['title'] = self.overview.short_description
        context['has_change_permission'] = request.user.has_perm('survey.change_survey')
        context['object'] = context['survey'] = (Survey.objects.prefetch_full_content().
                                                 get(pk=obj.pk))
        return render(request, 'survey/survey_admin_overview.html', context=context)
    overview.short_description = _("Overview a survey")
    overview.label = _("Overview")

    def export(self, request, obj):
        response = HttpResponse(content_type='text/csv')
        filename = "export-%s.csv" % (str(obj), )
        response['Content-Disposition'] = 'attachment; filename="%s"' % (filename, )

        def get_key(subquestion):
            return "{title}:{pk}".format(title=subquestion.name, pk=subquestion.pk)

        fieldnames = ['Health fund', 'Hospital', 'Identifier', 'Voivodeship', 'City']
        fieldnames += [get_key(subquestion) for subquestion in Subquestion.objects.
                       filter(question__category__survey=obj).all()]
        answer_qs = (Answer.objects.filter(participant__survey=obj).
                     select_related('participant__health_fund').
                     select_related('subquestion').
                     select_related('hospital').all())
        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()

        def key(x):
            return (x.participant.health_fund, x.hospital)

        for (participant, hospital), g in groupby(answer_qs, key):
            row = {'Health fund': participant,
                   'Hospital': hospital,
                   'Identifier': hospital.identifier,
                   'Voivodeship': hospital.voivodeship,
                   'City': hospital.city}
            row.update({get_key(answer.subquestion): answer.answer
                        for answer in g
                        if get_key(answer.subquestion) in fieldnames})
            writer.writerow(row)
        return response

    def stats(self, request, obj):
        context = {}
        context['opts'] = self.opts
        context['original'] = obj
        context['title'] = self.stats.short_description
        context['object'] = obj
        context['has_change_permission'] = request.user.has_perm('survey.change_survey')
        context['survey'] = obj
        qs = (Participant.objects.filter(survey=obj).
              with_progress_stats().
              select_related('health_fund').all())
        context['participant_list'] = qs
        context['sum_fill_count'] = sum(x.get_answer_count() for x in qs)
        context['sum_required_count'] = sum(x.get_required_count() for x in qs)
        context['sum_progress'] = context['sum_fill_count'] / context['sum_required_count'] * 100
        return render(request, 'survey/survey_admin_stats.html', context=context)
    stats.short_description = _("Statistics of progress of analysis")
    stats.label = _("Statistics")

    def update_subquestion_count(modeladmin, request, queryset):
        count = 0
        for survey in queryset.with_db_subquestion_count().all():
            survey.subquestion_count = survey.db_subquestion_count
            survey.save(update_fields=['subquestion_count'])
            count = count + 1
        messages.success(request, 'Subquestion count of {0} surveys was updated.'.format(count))


admin.site.register(Survey, SurveyAdmin)


class ParticipantAdmin(ImportExportMixin, VersionAdmin):
    '''
        Admin View for Participant
    '''

    def solve_url(self, obj):
        url = 'http://%s%s' % (
            Site.objects.get_current().domain, obj.get_absolute_url())
        return '<a href="%s">%s</a>' % (url, url)
    solve_url.allow_tags = True
    solve_url.short_description = _("Solve url")
    list_display = ('pk', 'survey', 'health_fund', 'password', 'solve_url', 'get_progress_display')
    list_filter = ('survey', 'health_fund')
    readonly_fields = ('answer_count',)
    resource_class = ParticipantResource
    actions = ['update_answer_count', ]

    def get_queryset(self, *args, **kwargs):
        qs = super(ParticipantAdmin, self).get_queryset(*args, **kwargs)
        return qs.with_progress_stats()

    def get_progress_display(self, obj):
        return obj.get_progress_display()
    get_progress_display.admin_order_field = 'progress'
    get_progress_display.short_description = _('Progress')

    def update_answer_count(modeladmin, request, queryset):
        count = 0
        for participant in queryset.with_db_answer_count().all():
            participant.answer_count = participant.db_answer_count
            participant.save(update_fields=['answer_count'])
            count = count + 1
        messages.success(request, 'Answer count of {0} participants was updated.'.format(count))


admin.site.register(Participant, ParticipantAdmin)


class QuestionInline(admin.TabularInline):
    '''
        Tabular Inline View for Question
    '''
    model = Question


class CategoryAdmin(DjangoObjectActions, VersionAdmin):
    '''
        Admin View for Category
    '''
    list_display = ('name', 'survey')
    list_filter = ('survey',)
    search_fields = ('name',)
    inlines = [
        QuestionInline
    ]
    change_actions = ['parent_edit']

    def parent_edit(self, request, obj):
        return redirect(reverse('admin:survey_survey_change', args=[str(obj.survey_id)]))
    parent_edit.short_description = _("Edit survey")
    parent_edit.label = _("Edit a parent survey")


admin.site.register(Category, CategoryAdmin)


class SubquestionInline(admin.TabularInline):
    '''
        Tabular Inline View for Subquestion
    '''
    model = Subquestion


class QuestionAdmin(DjangoObjectActions, VersionAdmin):
    '''
        Admin View for Question
    '''
    list_display = ('name', 'created', 'modified', 'ordering')
    list_filter = ('category__survey',)
    inlines = [
        SubquestionInline,
    ]
    search_fields = ('name',)

    change_actions = ['parent_edit']

    def parent_edit(self, request, obj):
        return redirect(reverse('admin:survey_category_change', args=[str(obj.category_id)]))
    parent_edit.short_description = _("Edit category")
    parent_edit.label = _("Edit a parent category")


admin.site.register(Question, QuestionAdmin)


class AnswerInline(admin.TabularInline):
    '''
        Stacked Inline View for Answer
    '''
    model = Answer


class SubquestionAdmin(DjangoObjectActions, VersionAdmin):
    '''
        Admin View for Subquestion
    '''
    list_display = ('name', 'question', 'kind', 'ordering')
    list_filter = ('question__category__survey',)
    inlines = [
        AnswerInline,
    ]
    change_actions = ['parent_edit']

    def parent_edit(self, request, obj):
        return redirect(reverse('admin:survey_question_change', args=[str(obj.question_id)]))
    parent_edit.short_description = _("Edit question")
    parent_edit.label = _("Edit a parent question")


admin.site.register(Subquestion, SubquestionAdmin)


class AnswerAdmin(VersionAdmin):
    '''
        Admin View for Answer
    '''
    list_display = ('answer', 'participant', 'subquestion', 'hospital')
    list_filter = ('participant', 'subquestion__question', 'subquestion', 'hospital',)


admin.site.register(Answer, AnswerAdmin)
