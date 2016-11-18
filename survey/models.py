import random

from autoslug.fields import AutoSlugField
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Count
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
    def answer_status(self, participant):
        qs = self.filter(answer__participant=1).annotate(answer_count=Count('answer'))
        qs = qs.annotate(status=models.Case(
            models.When(answer_count=0, then=models.Value(False)),
            default=models.Value(True),
            output_field=models.BooleanField())
        )
        return qs


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
    participants = models.ManyToManyField(NationalHealtFund, through="Participant")
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
            log.append("[FAIL] Entities in %s survey is missing" % (str(self),))
        else:
            log.append("[OK] %d category in %s exists" % (category_count, str(self)))

        for category in self.category_set.all():
            log.append("Audit %s category" % (str(category)))
            question_count = len(category.question_set.all())
            if not question_count:
                log.append("[FAIL] Question in %s category is missing" % (str(category), ))
            else:
                log.append("[OK] %d question in %s category exists" % (question_count,
                                                                       str(category), ))

            for question in category.question_set.all():
                log.append("Audit %s question" % (str(question)))
                subquestion_count = len(question.subquestion_set.all())
                if not subquestion_count:
                    log.append("[FAIL] Subquestion in %s question is missing" % (str(question), ))
                else:
                    log.append("[OK] %d subquestion in %s question exists" % (subquestion_count,
                                                                              str(question)))
        return log

    class Meta:
        verbose_name = _("Survey")
        verbose_name_plural = _("Surveys")
        ordering = ['created', ]

    def __str__(self):
        return self.title


class Participant(TimeStampedModel):
    health_fund = models.ForeignKey(NationalHealtFund, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    password = models.CharField(verbose_name=_("Password"), default=get_secret, max_length=15)

    def get_absolute_url(self, *args, **kwargs):
        return reverse('survey:list', kwargs={'participant': str(self.id),
                                              'password': self.password})

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
    ordering = models.PositiveSmallIntegerField(verbose_name=_("Order"), default=1)
    objects = CategoryQuerySet.as_manager()

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['ordering', 'created', ]

    def __str__(self):
        return self.name


class QuestionQuerySet(models.QuerySet):
    pass


@python_2_unicode_compatible
class Question(TimeStampedModel):
    category = models.ForeignKey(to=Category, verbose_name=_("Category"))
    name = models.CharField(verbose_name=_("Name"), max_length=250)
    ordering = models.PositiveSmallIntegerField(verbose_name=_("Order"), default=1)
    objects = QuestionQuerySet.as_manager()

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ['ordering', 'created', ]

    def __str__(self):
        return self.name


class SubquestionQuerySet(models.QuerySet):
    pass


@python_2_unicode_compatible
class Subquestion(TimeStampedModel):
    question = models.ForeignKey(to=Question, verbose_name=_("Question"))
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    ordering = models.PositiveSmallIntegerField(verbose_name=_("Order"), default=1)
    objects = SubquestionQuerySet.as_manager()

    class Meta:
        verbose_name = _("Subquestion")
        verbose_name_plural = _("Subquestions")
        ordering = ['ordering', 'created', ]

    def __str__(self):
        return self.name


class AnswerQuerySet(models.QuerySet):
    pass


@python_2_unicode_compatible
class Answer(TimeStampedModel):
    participant = models.ForeignKey(Participant, verbose_name=_("Participant"))
    subquestion = models.ForeignKey(Subquestion, verbose_name=_("Subquestions"))
    hospital = models.ForeignKey(Hospital, verbose_name=_("Hospital"))
    answer = models.TextField(verbose_name=_("Answer"))
    objects = AnswerQuerySet.as_manager()

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")
        ordering = ['created', ]

    def __str__(self):
        return "%d in %d said %s" % (self.hospital_id, self.subquestion_id, self.answer)
