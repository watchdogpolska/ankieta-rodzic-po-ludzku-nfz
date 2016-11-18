import random

from autoslug.fields import AutoSlugField
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel


def get_secret():
    return random.randint(10**4, 10**5 - 1)


class NationalHealtFundQuerySet(models.QuerySet):
    pass


@python_2_unicode_compatible
class NationalHealtFund(TimeStampedModel):
    name = models.CharField(verbose_name=_("Name"), max_length=50)
    email = models.EmailField(verbose_name=_("E-mail"), blank=True)
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=15)
    objects = NationalHealtFundQuerySet.as_manager()

    class Meta:
        verbose_name = _("National Healt Fund")
        verbose_name_plural = _("National Healt Funds")
        ordering = ['created', ]

    def __str__(self):
        return self.name


class HospitalQuerySet(models.QuerySet):
    pass


@python_2_unicode_compatible
class Hospital(TimeStampedModel):
    health_fund = models.ForeignKey(NationalHealtFund, verbose_name=_("National Healt Fund"))
    name = models.CharField(verbose_name=_("Name"), max_length=250)
    email = models.EmailField(verbose_name=_("E-mail"))
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=250)
    objects = HospitalQuerySet.as_manager()

    class Meta:
        verbose_name = _("Hospital")
        verbose_name_plural = _("Hospitals")
        ordering = ['created', ]

    def __str__(self):
        return self.name


class SurveyQuerySet(models.QuerySet):

    def prefetch_full_content(self):
        return self.prefetch_related('category_set__question_set__subquestion_set')


@python_2_unicode_compatible
class Survey(TimeStampedModel):
    title = models.CharField(verbose_name=_("Title"), max_length=250)
    slug = AutoSlugField(populate_from='title', verbose_name=_("Slug"), unique=True)
    welcome_text = models.TextField(verbose_name=_("Welcome text"), blank=True)
    end_text = models.TextField(verbose_name=_("End text"), blank=True)
    submit_text = models.TextField(verbose_name=_("Submit text"), blank=True)
    participants = models.ManyToManyField(Hospital, through="Participant")
    objects = SurveyQuerySet.as_manager()

    def perform_audit(self):
        log = []
        log.append("Audit %s survey" % (str(self)))
        # Entities auditing
        entities_count = len(self.participants.all())
        if not entities_count:
            log.append("[FAIL] Entities in survey is required")
        else:
            log.append("[OK] %d entities exists" % (entities_count, ))

        # Category auditing:
        category_count = len(self.category_set.all())
        if not category_count:
            log.append("[FAIL] Entities in survey is required")
        else:
            log.append("[OK] %d category exists" % (category_count, ))

        for category in self.category_set.all():
            log.append("Audit %s category" % (str(category)))
            question_count = len(category.question_set.all())
            if not question_count:
                log.append("[FAIL] Question in each category is required")
            else:
                log.append("[OK] %d category exists" % (question_count, ))

            for question in category.question_set.all():
                log.append("Audit %s question" % (str(question)))
                subquestion_count = len(question.subquestion_set.all())
                if not subquestion_count:
                    log.append("[FAIL] Subquestion for each question is required")
                else:
                    log.append("[OK] %d subquestion exists" % (subquestion_count, ))
        return log

    class Meta:
        verbose_name = _("Survey")
        verbose_name_plural = _("Surveys")
        ordering = ['created', ]

    def __str__(self):
        return self.title


class Participant(TimeStampedModel):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    password = models.CharField(verbose_name=_("Password"), default=get_secret, max_length=15)

    class Meta:
        verbose_name = _("Participant")
        verbose_name_plural = _("Participants")
        ordering = ['created']


class CategoryQuerySet(models.QuerySet):
    pass


@python_2_unicode_compatible
class Category(TimeStampedModel):
    survey = models.ForeignKey(to=Survey, verbose_name=_("Survey"))
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    description = models.TextField(verbose_name=_("Description"), blank=True)
    objects = CategoryQuerySet.as_manager()

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['created', ]

    def __str__(self):
        return self.name


class QuestionQuerySet(models.QuerySet):
    pass


@python_2_unicode_compatible
class Question(TimeStampedModel):
    category = models.ForeignKey(to=Category, verbose_name=_("Category"))
    name = models.CharField(verbose_name=_("Name"), max_length=250)
    objects = QuestionQuerySet.as_manager()

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ['created', ]

    def __str__(self):
        return self.name


class SubquestionQuerySet(models.QuerySet):
    pass


@python_2_unicode_compatible
class Subquestion(TimeStampedModel):
    question = models.ForeignKey(to=Question, verbose_name=_("Question"))
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    objects = SubquestionQuerySet.as_manager()

    class Meta:
        verbose_name = _("Subquestion")
        verbose_name_plural = _("Subquestions")
        ordering = ['created', ]

    def __str__(self):
        return self.name


class AnswerQuerySet(models.QuerySet):
    pass


@python_2_unicode_compatible
class Answer(TimeStampedModel):
    participant = models.ForeignKey(Participant, verbose_name=_("Participant"))
    subquestion = models.ForeignKey(Subquestion, verbose_name=_("Subquestions"))
    answer = models.TextField(verbose_name=_("Answer"))
    objects = AnswerQuerySet.as_manager()

    def hospital(self):
        return self.entity.hospital

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")
        ordering = ['created', ]

    def __str__(self):
        return "%d in %d said %s" % (self.hospital_id, self.question_id, self.answer)
