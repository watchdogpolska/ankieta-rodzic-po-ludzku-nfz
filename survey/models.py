import random
from collections import namedtuple

from autoslug.fields import AutoSlugField
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from tinymce.models import HTMLField

LogEntry = namedtuple('LogEntry', ['status', 'text'])
LinkedHospital = namedtuple('LinkedHospital', ['obj', 'link', 'status'])


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

    def answer_fetch(self, participant):
        prefetch = models.Prefetch(lookup='answer_set',
                                   to_attr='answer_participant',
                                   queryset=Answer.objects.filter(participant=participant))
        return self.prefetch_related(prefetch)

    def linked(self, participant, password):
        linked_hospitals = []
        for hospital in self:
            link = reverse('survey:survey', kwargs={'password': password,
                                                    'participant': participant,
                                                    'hospital': hospital.pk})
            link = 'http://%s%s' % (Site.objects.get_current().domain, link)
            linked = LinkedHospital(obj=hospital,
                                    link=link,
                                    status=len(hospital.answer_participant) > 0)
            linked_hospitals.append(linked)
        return linked_hospitals


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
    welcome_text = HTMLField(verbose_name=_("Welcome text"), blank=True)
    instruction = HTMLField(verbose_name=_("Instruction"), blank=True)
    end_text = HTMLField(verbose_name=_("End text"), blank=True)
    submit_text = HTMLField(verbose_name=_("Submit text"), blank=True)
    participants = models.ManyToManyField(NationalHealtFund, through="Participant")
    objects = SurveyQuerySet.as_manager()

    def _count_msg(self, obj, attribute, found=None, missing=None):
        count = len(getattr(obj, attribute).all())
        rel_name = getattr(obj, attribute).model._meta.verbose_name
        obj_name = obj._meta.verbose_name
        missing = missing or "%s in %%s %s is missing" % (rel_name, obj_name)
        found = found or "%%d %s exists in %%s %s" % (rel_name, obj_name)
        if count:
            return LogEntry(True, found % (count, obj))
        return LogEntry(False, missing % (obj))

    def perform_audit(self):
        log = []
        log.append(LogEntry(None, "Audit %s survey" % (str(self))))
        # Entities auditing
        log.append(self._count_msg(self, 'participants'))
        log.append(self._count_msg(self, 'category_set'))

        for category in self.category_set.all():
            log.append(LogEntry(None, "Audit %s category" % (str(category))))
            log.append(self._count_msg(category, 'question_set'))

            for question in category.question_set.all():
                log.append(LogEntry(None, "Audit %s question" % (str(question))))
                log.append(self._count_msg(question, 'subquestion_set'))
        return log

    class Meta:
        verbose_name = _("Survey")
        verbose_name_plural = _("Surveys")
        ordering = ['created', ]

    def __str__(self):
        return self.title


class ParticipantQuerySet(models.QuerySet):

    def with_survey(self):
        return self.prefetch_related('survey__category_set__question_set__subquestion_set')


class Participant(TimeStampedModel):
    health_fund = models.ForeignKey(NationalHealtFund, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    password = models.CharField(verbose_name=_("Password"), default=get_secret, max_length=15)
    objects = ParticipantQuerySet.as_manager()

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
    KIND_INT = 'int'
    KIND_TEXT = 'text'
    KIND_LTEXT = 'ltext'
    KIND = ((KIND_INT, 'Integer'),
            (KIND_TEXT, 'Text'),
            (KIND_LTEXT, 'Long text'))
    question = models.ForeignKey(to=Question, verbose_name=_("Question"))
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    ordering = models.PositiveSmallIntegerField(verbose_name=_("Order"), default=1)
    kind = models.CharField(verbose_name=_("Kind of answer"),
                            choices=KIND,
                            max_length=5,
                            default=KIND_TEXT)
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
        ordering = ['participant', 'hospital', 'subquestion']

    def __str__(self):
        return str(self.answer)
