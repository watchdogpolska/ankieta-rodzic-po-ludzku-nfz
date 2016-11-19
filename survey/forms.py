from collections import namedtuple

from django import forms

from .models import Answer

Group = namedtuple('Group', ['obj', 'set'])


class SurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.participant = kwargs.pop('participant')
        self.hospital = kwargs.pop('hospital')

        self.survey = self.participant.survey

        answer_qs = Answer.objects.filter(participant=self.participant,
                                          hospital=self.hospital).all()
        initial = {x.subquestion_id: x.answer for x in answer_qs}

        super(SurveyForm, self).__init__(*args, **kwargs)
        for category in self.survey.category_set.all():
            for question in category.question_set.all():
                for subquestion in question.subquestion_set.all():
                    key = self.get_key(subquestion)
                    field = forms.CharField(label=subquestion.name,
                                            initial=initial.get(subquestion.pk, ''))
                    self.fields[key] = field

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

    def save(self):
        objs = []
        for category in self.survey.category_set.all():
            for question in category.question_set.all():
                for subquestion in question.subquestion_set.all():
                    obj, created = Answer.objects.update_or_create(
                        participant=self.participant,
                        subquestion=subquestion,
                        hospital=self.hospital,
                        defaults={'answer': self.cleaned_data[self.get_key(subquestion)]},
                    )
                    objs.append(obj)
        return obj
