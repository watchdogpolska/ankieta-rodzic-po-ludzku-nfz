import factory
from . import models


class NationalHealtFundFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.NationalHealtFund

    name = factory.Sequence(lambda n: "NFZ-%03d" % n)
    email = factory.Sequence(lambda n: "NFZ@%03d.com" % n)
    identifier = factory.Sequence(lambda n: "NFZ-%03d" % n)


class HospitalFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Hospital

    health_fund = factory.SubFactory(NationalHealtFundFactory)
    name = factory.Sequence(lambda n: "Host-%03d" % n)
    email = factory.Sequence(lambda n: "NFZ@%03d.com" % n)
    identifier = factory.Sequence(lambda n: "NFZ-%03d" % n)


class SurveyFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Survey

    title = factory.Sequence(lambda n: "Survey-%03d" % n)
    welcome_text = factory.Sequence(lambda n: "NFZ@%03d.com" % n)
    end_text = factory.Sequence(lambda n: "NFZ-%03d" % n)
    submit_text = factory.Sequence(lambda n: "NFZ %03d" % n)

    @factory.post_generation
    def participants(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for health_fund in extracted:
                models.Participant.objects.create(health_fund=health_fund,
                                                  survey=self)


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Category

    survey = factory.SubFactory(SurveyFactory)
    name = factory.Sequence(lambda n: "Cat-%03d" % n)
    description = factory.Sequence(lambda n: "Cat-dsc-%03d" % n)


class ParticipantFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Participant

    health_fund = factory.SubFactory(NationalHealtFundFactory)
    survey = factory.SubFactory(SurveyFactory)


class QuestionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Question

    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: "Question-%03d" % n)


class SubquestionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Subquestion

    question = factory.SubFactory(QuestionFactory)
    name = factory.Sequence(lambda n: "Subquestion-%03d" % n)


class AnswerFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Answer
    participant = factory.SubFactory(ParticipantFactory,
                                     survey=factory.SelfAttribute('..subquestion.question.category.survey'))
    subquestion = factory.SubFactory(SubquestionFactory)
    hospital = factory.SubFactory(HospitalFactory)
    answer = factory.Sequence(lambda n: n)
