from collections import namedtuple

from ankieta_nfz.users.models import User
from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from .models import Answer, Hospital, Subquestion

Group = namedtuple('Group', ['obj', 'set'])


class SurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.participant = kwargs.pop('participant')
        self.hospital = kwargs.pop('hospital')
        self.user = kwargs.pop('user', None)

        self.survey = self.participant.survey

        answer_qs = Answer.objects.filter(participant=self.participant,
                                          hospital=self.hospital).all()
        self.initial = {x.subquestion_id: x.answer for x in answer_qs}

        super(SurveyForm, self).__init__(*args, **kwargs)
        for category in self.survey.category_set.all():
            for question in category.question_set.all():
                for subquestion in question.subquestion_set.all():
                    key = self.get_key(subquestion)
                    field = self.get_field(subquestion)
                    self.fields[key] = field

    def get_field(self, subquestion):
        if subquestion.kind == Subquestion.KIND_INT:
            return forms.IntegerField(label=subquestion.name,
                                      initial=self.initial.get(subquestion.pk, ''))
        if subquestion.kind == Subquestion.KIND_TEXT:
            return forms.CharField(label=subquestion.name,
                                   initial=self.initial.get(subquestion.pk, ''))
        if subquestion.kind == Subquestion.KIND_LTEXT:
            return forms.CharField(label=subquestion.name,
                                   initial=self.initial.get(subquestion.pk, ''),
                                   widget=forms.widgets.Textarea())

    def get_key(self, subquestion):
        return 'sq-{subquestion}'.format(subquestion=subquestion.pk)

    def grouped_fields(self):
        output = []
        for category in self.survey.category_set.all():
            question_set = []
            for question in category.question_set.all():
                subquestion_set = []
                for subquestion in question.subquestion_set.all():
                    field = self[self.get_key(subquestion)]
                    subquestion_set.append(Group(subquestion, field))
                question_set.append(Group(question, subquestion_set))
            output.append(Group(category, question_set))
        return output

    def save_model(self):
        self.objs = []
        self.createds = []
        for category in self.survey.category_set.all():
            for question in category.question_set.all():
                for subquestion in question.subquestion_set.all():
                    obj, created = Answer.objects.update_or_create(
                        participant=self.participant,
                        subquestion=subquestion,
                        hospital=self.hospital,
                        defaults={'answer': self.cleaned_data[self.get_key(subquestion)]},
                    )
                    self.objs.append(obj)
                    self.createds.append(created)

    def send_notification(self):
        output = []
        index = 0
        for category in self.survey.category_set.all():
            question_set = []
            for question in category.question_set.all():
                subquestion_set = []
                for subquestion in question.subquestion_set.all():
                    field = [self.objs[index], self.createds[index]]
                    subquestion_set.append(Group(subquestion, field))
                    index += 1
                question_set.append(Group(question, subquestion_set))
            output.append(Group(category, question_set))
        linked_list = Hospital.objects.answer_fetch(self.participant).linked(participant=self.participant.pk,
                                                                             password=self.participant.password)
        linked_list_left = [x for x in linked_list if x.status is not True]
        linked_done = len(linked_list_left)
        linked_total = len(linked_list)
        linked_left = linked_total - linked_done
        context = {'object_list': output,
                   'linked_list': linked_list,
                   'linked_list_left': linked_list_left,
                   'linked_done': linked_done,
                   'linked_total': linked_total,
                   'linked_left': linked_left,
                   'hospital': self.hospital,
                   'participant': self.participant}
        content = render_to_string('survey/survey_email.html', context)
        recipients = [x.email for x in User.objects.filter(is_staff=True, notification=True).all()]
        if not self.user.is_staff:
            recipients += [self.participant.health_fund.email, ]
        return send_mail(
            _('Answer confirmation'),
            content,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )

    def save(self):
        self.save_model()
        self.send_notification()
        return self.objs
