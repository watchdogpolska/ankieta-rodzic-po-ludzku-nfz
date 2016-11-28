from collections import namedtuple

from ankieta_nfz.users.models import User
from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from .models import Answer, Hospital, Participant, Subquestion

Group = namedtuple('Group', ['obj', 'set'])


class values_or_integer_validator(object):

    def __init__(self, values, code='invalid'):
        self.values = values
        self.code = code

    def get_message(self, value):
        values_str = _(" and ").join('"%s"'.format(x) for x in self.values)

        return _('The value entered "{value}" is incorrect. ' +
                 'Only allowable values of {values} and numbers.').format(value=value,
                                                                          values=values_str)

    def valid_int(self, value):
        try:
            int(value)
        except ValueError:
            return False
        return True

    def __call__(self, value):
        """
        Validates that the input is some values or it is integer
        """
        if not (value in self.values or self.valid_int(value)):
            raise ValidationError(self.get_message(value), code=self.code)


class FieldMixin(object):

    def get_field(self, subquestion, *args, **kwargs):
        if subquestion.kind == Subquestion.KIND_INT:
            return forms.IntegerField(label=subquestion.name,
                                      initial=self.get_initial(subquestion, *args, **kwargs))
        if subquestion.kind == Subquestion.KIND_TEXT:
            return forms.CharField(label=subquestion.name,
                                   initial=self.get_initial(subquestion, *args, **kwargs))
        if subquestion.kind == Subquestion.KIND_LTEXT:
            return forms.CharField(label=subquestion.name,
                                   initial=self.get_initial(subquestion, *args, **kwargs),
                                   widget=forms.widgets.Textarea())
        if subquestion.kind == Subquestion.KIND_VINT:
            return forms.CharField(label=subquestion.name,
                                   initial=self.get_initial(subquestion, *args, **kwargs),
                                   validators=[values_or_integer_validator(['b/d', 'brak danych'])])

    def get_recipient(self):
        recipients = [x.email for x in User.objects.filter(is_staff=True, notification=True).all()]
        if not self.user.is_staff and self.participant.health_fund.email:
            recipients += [self.participant.health_fund.email, ]
        return recipients


class SurveyForm(FieldMixin, forms.Form):

    def __init__(self, *args, **kwargs):
        self.participant = kwargs.pop('participant')
        self.hospital = kwargs.pop('hospital')
        self.user = kwargs.pop('user', None)

        self.survey = self.participant.survey

        answer_qs = Answer.objects.filter(participant=self.participant,
                                          hospital=self.hospital).all()
        self.initial_sq = {x.subquestion_id: x.answer for x in answer_qs}

        super(SurveyForm, self).__init__(*args, **kwargs)
        for category in self.survey.category_set.all():
            for question in category.question_set.all():
                for subquestion in question.subquestion_set.all():
                    key = self.get_key(subquestion)
                    field = self.get_field(subquestion)
                    self.fields[key] = field

    def get_initial(self, subquestion):
        return self.initial_sq.get(subquestion.pk, '')

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
                    subquestion_set.append((subquestion, field))
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
        recipients = self.get_recipient()
        if not recipients:
            return

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
        linked_list = (Hospital.objects.
                       answer_fetch(self.participant).
                       linked(participant=self.participant.pk,
                              password=self.participant.password))
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


class ParticipantForm(FieldMixin, forms.Form):

    def __init__(self, *args, **kwargs):
        self.participant = kwargs.pop('participant')
        self.user = kwargs.pop('user', None)

        self.survey = self.participant.survey
        self.hospitals = self.participant.health_fund.hospital_set.all()
        self.answer_qs = Answer.objects.filter(participant=self.participant).all()
        self.initial_sq = {(x.hospital_id, x.subquestion_id): x.answer
                           for x in self.answer_qs}

        super(ParticipantForm, self).__init__(*args, **kwargs)
        for category in self.survey.category_set.all():
            for question in category.question_set.all():
                for subquestion in question.subquestion_set.all():
                    for hospital in self.hospitals:
                        key = self.get_key(hospital, subquestion)
                        field = self.get_field(subquestion=subquestion,
                                               hospital=hospital)
                        self.fields[key] = field

    def get_key(self, hospital, subquestion):
        return 'h-{hospital}-sq-{subquestion}'.format(hospital=hospital.pk,
                                                      subquestion=subquestion.pk)

    def get_initial(self, subquestion, hospital):
        return self.initial_sq.get((hospital.id, subquestion.id), '')

    def grouped_fields(self):
        output = []
        for category in self.survey.category_set.all():
            question_set = []
            for question in category.question_set.all():
                subquestion_set = [x for x in question.subquestion_set.all()]
                hospital_set = []
                for hospital in self.hospitals:
                    hospitalsubquestion_set = []

                    for subquestion in subquestion_set:
                        field = self[self.get_key(hospital, subquestion)]
                        hospitalsubquestion_set.append(field)
                    hospital_set.append((hospital, hospitalsubquestion_set))

                question_set.append((question, subquestion_set, hospital_set))
            output.append(Group(category, question_set))
        return output

    def send_notification(self):
        recipients = self.get_recipient()
        if not recipients:
            return

        output = []
        answers = {(x.hospital_id, x.subquestion_id): x
                   for x in Answer.objects.filter(participant=self.participant).all()}

        for category in self.survey.category_set.all():
            question_set = []
            for question in category.question_set.all():
                subquestions = [x for x in question.subquestion_set.all()]

                subquestion_set = []
                for subquestion in subquestions:
                    answer_set = []
                    for hospital in self.hospitals:
                        data = answers[(hospital.pk, subquestion.pk)].answer
                        answer_set.append((hospital, data))
                    subquestion_set.append(Group(subquestion, answer_set))

                question_set.append((question, subquestion_set))
            output.append(Group(category, question_set))
        context = {'object_list': output,
                   'participant': self.participant}
        content = render_to_string('survey/participant_email.html', context)
        return send_mail(
            _('Answer confirmation'),
            content,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )

    def save_model(self):
        self.objs = []
        self.createds = []
        to_bulk_create = []

        answers = {(x.hospital_id, x.subquestion_id): x
                   for x in Answer.objects.filter(participant=self.participant).all()}
        for category in self.survey.category_set.all():
            for question in category.question_set.all():
                for subquestion in question.subquestion_set.all():
                    for hospital in self.participant.health_fund.hospital_set.all():
                        data = self.cleaned_data[self.get_key(hospital, subquestion)]
                        try:
                            a = answers[(hospital.pk, subquestion.pk)]
                            if a.answer != str(data):  # if any changes
                                a.answer = data
                                a.save()
                        except KeyError:
                            to_bulk_create.append(Answer(participant=self.participant,
                                                         subquestion=subquestion,
                                                         hospital=hospital,
                                                         answer=data))
        Participant.objects.filter(pk=self.participant.pk).update(answer_count=F('answer_count') +
                                                                  len(to_bulk_create))
        Answer.objects.bulk_create(to_bulk_create)

    def save(self):
        self.save_model()
        self.send_notification()


class QuestionForm(FieldMixin, forms.Form):

    def __init__(self, *args, **kwargs):
        self.participant = kwargs.pop('participant')
        self.user = kwargs.pop('user', None)
        self.question = kwargs.pop('question')

        self.survey = self.participant.survey
        self.hospitals = self.participant.health_fund.hospital_set.all()
        self.answer_qs = Answer.objects.filter(participant=self.participant,
                                               subquestion__question=self.question).all()
        self.initial_sq = {(x.hospital_id, x.subquestion_id): x
                           for x in self.answer_qs}

        super(QuestionForm, self).__init__(*args, **kwargs)
        for subquestion in self.question.subquestion_set.all():
            for hospital in self.hospitals:
                key = self.get_key(hospital, subquestion)
                field = self.get_field(subquestion=subquestion,
                                       hospital=hospital)
                self.fields[key] = field

    def get_key(self, hospital, subquestion):
        return 'h-{hospital}-sq-{subquestion}'.format(hospital=hospital.pk,
                                                      subquestion=subquestion.pk)

    def get_initial(self, subquestion, hospital):
        if (hospital.id, subquestion.id) in self.initial_sq:
            return self.initial_sq[(hospital.id, subquestion.id)].answer
        return ''

    def grouped_fields(self):
        subquestion_set = [x for x in self.question.subquestion_set.all()]
        hospital_set = []
        for hospital in self.hospitals:
            hospitalsubquestion_set = []
            for subquestion in subquestion_set:
                field = self[self.get_key(hospital, subquestion)]
                hospitalsubquestion_set.append(field)
            hospital_set.append((hospital, hospitalsubquestion_set))
        return hospital_set

    def send_notification(self):
        recipients = self.get_recipient()
        if not recipients:
            return
        answers = {(x.hospital_id, x.subquestion_id): x
                   for x in Answer.objects.filter(participant=self.participant).all()}
        subquestions = [x for x in self.question.subquestion_set.all()]

        subquestion_set = []
        for subquestion in subquestions:
            answer_set = []
            for hospital in self.hospitals:
                data = answers[(hospital.pk, subquestion.pk)].answer
                answer_set.append((hospital, data))
            subquestion_set.append(Group(subquestion, answer_set))

        context = {'participant': self.participant,
                   'category': self.question.category,
                   'survey': self.survey,
                   'question': self.question,
                   'subquestion_set': subquestion_set}
        content = render_to_string('survey/question_email.html', context)

        return send_mail(
            _('Answer confirmation'),
            content,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )

    def save_model(self):
        to_bulk_create = []
        answers = {(x.hospital_id, x.subquestion_id): x for x in self.answer_qs}

        for subquestion in self.question.subquestion_set.all():
            for hospital in self.hospitals:
                data = self.cleaned_data[self.get_key(hospital, subquestion)]
                try:
                    a = answers[(hospital.pk, subquestion.pk)]
                    if a.answer != str(data):  # if any changes
                        a.answer = data
                        a.save()
                except KeyError:
                    to_bulk_create.append(Answer(participant=self.participant,
                                                 subquestion=subquestion,
                                                 hospital=hospital,
                                                 answer=data))
        Participant.objects.filter(pk=self.participant.pk).update(answer_count=F('answer_count') +
                                                                  len(to_bulk_create))
        Answer.objects.bulk_create(to_bulk_create)

    def save(self):
        self.save_model()
        self.send_notification()
