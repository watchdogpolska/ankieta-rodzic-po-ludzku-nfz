from ankieta_nfz.users.factories import UserFactory
from django.core import mail
from django.test import TestCase

from .factories import (AnswerFactory, CategoryFactory, HospitalFactory,
                        NationalHealtFundFactory, ParticipantFactory,
                        QuestionFactory, SubquestionFactory, SurveyFactory)
from .forms import SurveyForm
from .models import Subquestion


class NationalHealtFundFactoryTestCase(TestCase):

    def test_build(self):
        NationalHealtFundFactory()


class HospitalFactoryTestCase(TestCase):

    def test_build(self):
        HospitalFactory()


class SurveyFactoryTestCase(TestCase):

    def test_build(self):
        SurveyFactory()

    def test_build_with_participants(self):
        SurveyFactory(participants=NationalHealtFundFactory.create_batch(size=10))


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
        self.participant = ParticipantFactory(survey=self.question.category.survey)
        self.hospital = HospitalFactory(health_fund=self.participant.health_fund)

    def test_grouped_fields(self):
        form = SurveyForm(participant=self.participant,
                          hospital=self.hospital,
                          user=UserFactory())
        self.assertEqual(len(form.grouped_fields()), 1)
        self.assertEqual(len(form.grouped_fields()[0].set), 1)
        self.assertEqual(len(form.grouped_fields()[0].set[0].set), 5)

    def test_fields_count(self):
        form = SurveyForm(participant=self.participant,
                          hospital=self.hospital,
                          user=UserFactory())
        self.assertEqual(len(form.fields), 1 * 5)

    def test_save_create(self):
        data = {("sq-%d" % (x.pk)): x.pk for x in self.subquestions}
        form = SurveyForm(data,
                          participant=self.participant,
                          hospital=self.hospital,
                          user=UserFactory())
        self.assertEqual(form.is_valid(), True)

    def test_form_notification_contains_answer(self):
        TEXT = "1234xx" * 5
        data = {("sq-%d" % (x.pk)): x.pk for x in self.subquestions}
        data["sq-%d" % (self.subquestions[0].pk)] = TEXT
        form = SurveyForm(data,
                          participant=self.participant,
                          hospital=self.hospital,
                          user=UserFactory())
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(TEXT, mail.outbox[0].body)

    def test_form_send_to_staffs(self):
        u = UserFactory(is_staff=True, notification=True)
        data = {("sq-%d" % (x.pk)): x.pk for x in self.subquestions}
        form = SurveyForm(data,
                          participant=self.participant,
                          hospital=self.hospital,
                          user=UserFactory())
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(u.email, mail.outbox[0].to)

    def test_send_notification_to_health_fund_for_user(self):
        data = {("sq-%d" % (x.pk)): x.pk for x in self.subquestions}
        form = SurveyForm(data,
                          participant=self.participant,
                          hospital=self.hospital,
                          user=UserFactory(is_staff=False))
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.participant.health_fund.email)

    def test_skip_notification_to_health_fund_for_staff_user(self):
        data = {("sq-%d" % (x.pk)): x.pk for x in self.subquestions}
        form = SurveyForm(data,
                          participant=self.participant,
                          hospital=self.hospital,
                          user=UserFactory(is_staff=False))
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.participant.health_fund.email)

    def test_integer_field_validation(self):
        sq = SubquestionFactory(question=self.question,
                                kind=Subquestion.KIND_INT)
        data = {("sq-%d" % (x.pk)): x.pk for x in self.subquestions}
        data['sq-%d' % (sq.pk)] = 'SOME_TEXT'
        form = SurveyForm(data,
                          participant=self.participant,
                          hospital=self.hospital,
                          user=UserFactory())
        self.assertEqual(form.is_valid(), False)

    def test_support_initial(self):
        answer = AnswerFactory(answer="Unique-answer-content",
                               subquestion=self.subquestions[0],
                               participant=self.participant,
                               hospital=self.hospital)
        form = SurveyForm(participant=self.participant,
                          hospital=self.hospital,
                          user=UserFactory())
        self.assertIn(answer.answer, form.as_p())
