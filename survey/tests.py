from ankieta_nfz.users.factories import UserFactory
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase

from .factories import (AnswerFactory, CategoryFactory, HospitalFactory,
                        NationalHealtFundFactory, ParticipantFactory,
                        QuestionFactory, SubquestionFactory, SurveyFactory)
from .forms import (ParticipantForm, QuestionForm, SurveyForm,
                    values_or_integer_validator)
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


class SurveyFormTestCase(TestCase):

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


class ParticipantFormTestCase(TestCase):

    def setUp(self):
        self.question = QuestionFactory()
        self.subquestions = SubquestionFactory.create_batch(size=5, question=self.question)
        self.participant = ParticipantFactory(survey=self.question.category.survey)
        self.hospital = HospitalFactory(health_fund=self.participant.health_fund)

    def test_fields_count(self):
        form = ParticipantForm(participant=self.participant,
                               user=UserFactory())
        self.assertEqual(len(form.fields), 1 * 5)

    def test_save_create(self):
        data = {("h-%d-sq-%d" % (self.hospital.pk, x.pk)): x.pk for x in self.subquestions}
        form = ParticipantForm(data,
                               participant=self.participant,
                               user=UserFactory())
        self.assertEqual(form.is_valid(), True)

    def test_form_notification_contains_answer(self):
        TEXT = "1234xx" * 5
        data = {("h-%d-sq-%d" % (self.hospital.pk, x.pk)): x.pk for x in self.subquestions}
        data["h-%d-sq-%d" % (self.hospital.pk, self.subquestions[0].pk)] = TEXT
        form = ParticipantForm(data,
                               participant=self.participant,
                               user=UserFactory())
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(TEXT, mail.outbox[0].body)

    def test_form_send_to_staffs(self):
        u = UserFactory(is_staff=True, notification=True)
        data = {("h-%d-sq-%d" % (self.hospital.pk, x.pk)): x.pk for x in self.subquestions}
        form = ParticipantForm(data,
                               participant=self.participant,
                               user=UserFactory())
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(u.email, mail.outbox[0].to)

    def test_send_notification_to_health_fund_for_user(self):
        data = {("h-%d-sq-%d" % (self.hospital.pk, x.pk)): x.pk for x in self.subquestions}
        form = ParticipantForm(data,
                               participant=self.participant,
                               user=UserFactory(is_staff=False))
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.participant.health_fund.email)

    def test_skip_notification_to_health_fund_for_staff_user(self):
        data = {("h-%d-sq-%d" % (self.hospital.pk, x.pk)): x.pk for x in self.subquestions}
        form = ParticipantForm(data,
                               participant=self.participant,
                               user=UserFactory(is_staff=False))
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.participant.health_fund.email)

    def test_integer_field_validation(self):
        sq = SubquestionFactory(question=self.question,
                                kind=Subquestion.KIND_INT)
        data = {("h-%d-sq-%d" % (self.hospital.pk, x.pk)): x.pk for x in self.subquestions}
        data['h-%d-sq-%d' % (self.hospital.pk, sq.pk)] = 'SOME_TEXT'
        form = ParticipantForm(data,
                               participant=self.participant,
                               user=UserFactory())
        self.assertEqual(form.is_valid(), False)

    def test_support_initial(self):
        answer = AnswerFactory(answer="Unique-answer-content",
                               subquestion=self.subquestions[0],
                               participant=self.participant,
                               hospital=self.hospital)
        form = ParticipantForm(participant=self.participant,
                               user=UserFactory())
        self.assertIn(answer.answer, form.as_p())


class QuestionFormTestCase(TestCase):

    def setUp(self):
        self.question = QuestionFactory()
        self.subquestions = SubquestionFactory.create_batch(size=5, question=self.question)
        self.participant = ParticipantFactory(survey=self.question.category.survey)
        self.hospitals = HospitalFactory.create_batch(size=5,
                                                      health_fund=self.participant.health_fund)

    def _get_standard_data(self):
        return {("h-%d-sq-%d" % (h.pk, sq.pk)): (sq.pk * h.pk) % 17 for sq in self.subquestions
                for h in self.hospitals}

    def test_fields_count(self):
        form = QuestionForm(participant=self.participant,
                            question=self.question,
                            user=UserFactory())
        self.assertEqual(len(form.fields), 5 * 5)

    def test_save_create(self):
        data = self._get_standard_data()
        form = QuestionForm(data,
                            participant=self.participant,
                            question=self.question,
                            user=UserFactory())
        self.assertEqual(form.is_valid(), True)

    def test_form_notification_contains_answer(self):
        TEXT = "1234xx" * 5
        data = self._get_standard_data()
        data["h-%d-sq-%d" % (self.hospitals[0].pk, self.subquestions[0].pk)] = TEXT
        form = QuestionForm(data,
                            question=self.question,
                            participant=self.participant,
                            user=UserFactory())
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(TEXT, mail.outbox[0].body)

    def test_form_send_to_staffs(self):
        u = UserFactory(is_staff=True, notification=True)
        data = self._get_standard_data()
        form = QuestionForm(data,
                            question=self.question,
                            participant=self.participant,
                            user=UserFactory())
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(u.email, mail.outbox[0].to)

    def test_send_notification_to_health_fund_for_user(self):
        data = self._get_standard_data()
        form = QuestionForm(data,
                            question=self.question,
                            participant=self.participant,
                            user=UserFactory(is_staff=False))
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.participant.health_fund.email)

    def test_skip_notification_to_health_fund_for_staff_user(self):
        data = self._get_standard_data()
        form = QuestionForm(data,
                            question=self.question,
                            participant=self.participant,
                            user=UserFactory(is_staff=False))
        self.assertEqual(form.is_valid(), True)
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.participant.health_fund.email)

    def test_integer_field_validation(self):
        sq = SubquestionFactory(question=self.question,
                                kind=Subquestion.KIND_INT)
        data = self._get_standard_data()
        data['h-%d-sq-%d' % (self.hospitals[0].pk, sq.pk)] = 'SOME_TEXT'
        form = QuestionForm(data,
                            question=self.question,
                            participant=self.participant,
                            user=UserFactory())
        self.assertEqual(form.is_valid(), False)

    def test_values_or_integer_validation(self):
        TEST_CASES = {'123': True,
                      'b/d': True,
                      'BLABLA': False,
                      '': False}
        sq = SubquestionFactory(question=self.question,
                                kind=Subquestion.KIND_VINT)

        for value, result in TEST_CASES.items():
            data = self._get_standard_data()
            for hospital in self.hospitals:
                data['h-%d-sq-%d' % (hospital.pk, sq.pk)] = value
            form = QuestionForm(data,
                                question=self.question,
                                participant=self.participant,
                                user=UserFactory())
            self.assertEqual(form.is_valid(), result, 'Validation failed for {0}'.format(value))

    def test_support_initial(self):
        answer = AnswerFactory(answer="Unique-answer-content",
                               subquestion=self.subquestions[0],
                               participant=self.participant,
                               hospital=self.hospitals[0])
        form = QuestionForm(participant=self.participant,
                            question=self.question,
                            user=UserFactory())
        self.assertIn(answer.answer, form.as_p())


class ValidatorsTestCase(TestCase):

    def test_values_or_integer_validator(self):
        valid = ['-1', '255', 'b/d', 'aaa']
        invalid = ['xx', '255.2']

        validator = values_or_integer_validator(values=['b/d', 'aaa'])
        for value in valid:
            validator(value)
        for value in invalid:
            with self.assertRaises(expected_exception=ValidationError):
                validator(value)
