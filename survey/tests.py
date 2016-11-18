from django.test import TestCase

from .factories import (AnswerFactory, CategoryFactory, HospitalFactory,
                        NationalHealtFundFactory, ParticipantFactory,
                        QuestionFactory, SubquestionFactory, SurveyFactory)


class NationalHealtFundFactoryTestCase(TestCase):
    def test_is_build(self):
        NationalHealtFundFactory()


class HospitalFactoryTestCase(TestCase):
    def test_is_build(self):
        HospitalFactory()


class SurveyFactoryTestCase(TestCase):
    def test_is_build(self):
        SurveyFactory()


class CategoryFactoryTestCase(TestCase):
    def test_is_build(self):
        CategoryFactory()


class ParticipantFactoryTestCase(TestCase):
    def test_is_build(self):
        ParticipantFactory()


class QuestionFactoryTestCase(TestCase):
    def test_is_build(self):
        QuestionFactory()


class SubquestionFactoryTestCase(TestCase):
    def test_is_build(self):
        SubquestionFactory()


class AnswerFactoryTestCase(TestCase):
    def test_is_build(self):
        AnswerFactory()

    def test_consistent_survey(self):
        answer = AnswerFactory()
        self.assertEqual(answer.subquestion.question.category.survey,
                         answer.participant.survey)
