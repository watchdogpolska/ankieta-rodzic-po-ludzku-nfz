from django.test import TestCase

from .factories import (AnswerFactory, CategoryFactory, HospitalFactory,
                        NationalHealtFundFactory, ParticipantFactory,
                        QuestionFactory, SubquestionFactory, SurveyFactory)
from .forms import SurveyForm


class NationalHealtFundFactoryTestCase(TestCase):
    def test_build(self):
        NationalHealtFundFactory()


class HospitalFactoryTestCase(TestCase):
    def test_build(self):
        HospitalFactory()


class SurveyFactoryTestCase(TestCase):
    def test_build(self):
        SurveyFactory()


class CategoryFactoryTestCase(TestCase):
    def test_build(self):
        CategoryFactory()


class ParticipantFactoryTestCase(TestCase):
    def test_build(self):
        ParticipantFactory()


class QuestionFactoryTestCase(TestCase):
    def test_build(self):
        QuestionFactory()


class SubquestionFactoryTestCase(TestCase):
    def test_build(self):
        SubquestionFactory()


class AnswerFactoryTestCase(TestCase):
    def test_build(self):
        AnswerFactory()

    def test_consistent_survey(self):
        answer = AnswerFactory()
        self.assertEqual(answer.subquestion.question.category.survey,
                         answer.participant.survey)


class QuestionFormTestCase(TestCase):
    def setUp(self):
        self.question = QuestionFactory()
        self.subquestions = SubquestionFactory.create_batch(size=5, question=self.question)
        self.participant = ParticipantFactory()
        self.hospital = HospitalFactory(health_fund=self.participant.health_fund)

    def test_grouped_fields(self):
        form = SurveyForm(participant=self.participant,
                          survey=self.question.category.survey,
                          hospital=self.hospital)
        self.assertEqual(len(form.grouped_fields()), 1)
        self.assertEqual(len(form.grouped_fields()[0].set), 1)
        self.assertEqual(len(form.grouped_fields()[0].set[0].set), 5)

    def test_fields_count(self):
        form = SurveyForm(participant=self.participant,
                          survey=self.question.category.survey,
                          hospital=self.hospital)
        self.assertEqual(len(form.fields), 1 * 5)

    def test_save_create(self):
        data = {("sq-%d" % (x.pk)): x.pk for x in self.subquestions}
        form = SurveyForm(data,
                          participant=self.participant,
                          survey=self.question.category.survey,
                          hospital=self.hospital)
        self.assertEqual(form.is_valid(), True)
