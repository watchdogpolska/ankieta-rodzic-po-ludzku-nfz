from collections import namedtuple

from braces.views import FormValidMessageMixin
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.views.generic import FormView, ListView, TemplateView, View
from reversion.views import RevisionMixin

from .forms import ParticipantForm, QuestionForm, SurveyForm
from .models import Category, Hospital, Participant, Question, Survey

SurveyHospitalForm = namedtuple('SurveyHospitalForm', ['hospital', 'form'])


class ParticipantMixin(object):
    cached_participant = None

    @cached_property
    def participant(self):
        return getattr(self, 'cached_participant') or \
            get_object_or_404(Participant.objects.with_survey().with_hospital(),
                              password=self.kwargs['password'],
                              pk=self.kwargs['participant'])


class HospitalMixin(ParticipantMixin):
    model = Hospital

    def get_queryset(self, *args, **kwargs):
        qs = super(HospitalMixin, self).get_queryset(*args, **kwargs)
        qs = qs.filter(health_fund__participant=self.participant).all()
        qs = qs.answer_fetch(self.participant)
        return qs


class HospitalListView(HospitalMixin, ListView):
    model = Hospital
    template_name = 'survey/hospital_list.html'

    def get_print_url(self):
        return reverse('survey:print', kwargs={'password': self.kwargs['password'],
                                               'participant': self.kwargs['participant']})

    def get_context_data(self, **kwargs):
        context = super(HospitalListView, self).get_context_data(**kwargs)
        context['linked_hospitals'] = self.object_list.linked(**self.kwargs)
        context['print_url'] = self.get_print_url()
        context['participant'] = self.participant
        context['survey'] = self.participant.survey
        return context


class QuestionListView(ParticipantMixin, ListView):
    model = Category
    template_name = 'survey/question_list.html'

    def get_queryset(self, *args, **kwargs):
        qs = super(QuestionListView, self).get_queryset(*args, **kwargs)
        return (qs.select_related('survey').
                prefetch_related('question_set__subquestion_set').
                filter(survey=self.participant.survey_id))

    def get_print_url(self):
        return reverse('survey:print', kwargs={'password': self.kwargs['password'],
                                               'participant': self.kwargs['participant']})

    def get_context_data(self, **kwargs):
        context = super(QuestionListView, self).get_context_data(**kwargs)
        question_dict = self.participant.answer_set.as_question_dict()
        context['linked_categories'] = self.object_list.linked(question_dict=question_dict,
                                                               **self.kwargs)
        context['print_url'] = self.get_print_url()
        context['participant'] = self.participant
        context['survey'] = self.participant.survey
        return context


class HospitalSurveyView(ParticipantMixin, RevisionMixin, FormValidMessageMixin, FormView):
    form_class = SurveyForm
    template_name = 'survey/hospital_form.html'

    @cached_property
    def survey(self):
        return self.participant.survey

    @cached_property
    def hospital(self):
        return get_object_or_404(Hospital,
                                 pk=self.kwargs['hospital'],
                                 health_fund=self.participant.health_fund)

    def get_form_kwargs(self, *args, **kwargs):
        kw = super(HospitalSurveyView, self).get_form_kwargs(*args, **kwargs)
        kw['participant'] = self.participant
        kw['hospital'] = self.hospital
        kw['user'] = self.request.user
        return kw

    def get_survey_list_url(self):
        return reverse('survey:list', kwargs={'password': self.kwargs['password'],
                                              'participant': self.kwargs['participant']})

    def get_context_data(self, **kwargs):
        context = super(HospitalSurveyView, self).get_context_data(**kwargs)
        context['survey'] = self.survey
        context['hospital'] = self.hospital
        context['survey_list_url'] = self.get_survey_list_url()
        return context

    def get_success_url(self):
        return self.get_survey_list_url()

    def get_form_valid_message(self):
        return _("Answer for {hospital} was saved!").format(hospital=self.hospital)

    def form_valid(self, form, *args, **kwargs):
        form.save()
        return super(HospitalSurveyView, self).form_valid(form, *args, **kwargs)


class QuestionSurveyView(ParticipantMixin, RevisionMixin, FormValidMessageMixin, FormView):
    form_class = QuestionForm
    template_name = 'survey/question_form.html'

    @cached_property
    def survey(self):
        return self.participant.survey

    @cached_property
    def question(self):
        return get_object_or_404(Question.objects.select_related('category__survey').
                                 prefetch_related('subquestion_set'),
                                 pk=self.kwargs['question'])

    def get_form_kwargs(self, *args, **kwargs):
        kw = super(QuestionSurveyView, self).get_form_kwargs(*args, **kwargs)
        kw['participant'] = self.participant
        kw['question'] = self.question
        kw['user'] = self.request.user
        return kw

    def get_survey_list_url(self):
        return reverse('survey:list', kwargs={'password': self.kwargs['password'],
                                              'participant': self.kwargs['participant']})

    def get_survey_print_url(self):
        return reverse('survey:print', kwargs={'password': self.kwargs['password'],
                                               'participant': self.kwargs['participant']})

    def get_context_data(self, **kwargs):
        context = super(QuestionSurveyView, self).get_context_data(**kwargs)
        context['survey'] = self.survey
        context['question'] = self.question
        context['subquestion_set'] = self.question.subquestion_set.all()
        context['survey_list_url'] = self.get_survey_list_url()
        context['survey_print_url'] = self.get_survey_print_url()

        return context

    def get_success_url(self):
        if self.request.POST.get('next', 'yes') == 'yes':
            return self.get_next_question_url() or self.get_survey_list_url()
        return self.get_survey_list_url()

    def get_form_valid_message(self):
        return _("Answer for {question} was saved!").format(question=self.question)

    def get_question_list(self):
        for category in self.survey.category_set.all():
            for question in category.question_set.all():
                yield question.pk

    def get_next_question_url(self):
        question_list = list(self.get_question_list())
        print(question_list)
        index = question_list.index(self.question.pk)
        if index + 1 >= len(question_list):
            return None
        return reverse('survey:survey', kwargs={'password': self.participant.password,
                                                'participant': self.participant.pk,
                                                'question': question_list[index + 1]})

    def form_valid(self, form, *args, **kwargs):
        form.save()
        return super(QuestionSurveyView, self).form_valid(form, *args, **kwargs)


class ParticipantFormView(ParticipantMixin, RevisionMixin, FormValidMessageMixin, FormView):
    form_class = ParticipantForm
    template_name = 'survey/participant_form.html'

    def get_form_kwargs(self, *args, **kwargs):
        kw = super(ParticipantFormView, self).get_form_kwargs(*args, **kwargs)
        kw['participant'] = self.participant
        kw['user'] = self.request.user
        return kw

    def get_survey_list_url(self):
        return reverse('survey:list', kwargs={'password': self.kwargs['password'],
                                              'participant': self.kwargs['participant']})

    def get_survey_print_url(self):
        return reverse('survey:print', kwargs={'password': self.kwargs['password'],
                                               'participant': self.kwargs['participant']})

    def get_form_valid_message(self):
        return _("Answer was saved!")

    def get_success_url(self):
        return self.get_survey_list_url()

    def get_context_data(self, **kwargs):
        context = super(ParticipantFormView, self).get_context_data(**kwargs)
        context['participant'] = self.participant
        context['survey_print_url'] = self.get_survey_print_url()
        return context

    def form_valid(self, form, *args, **kwargs):
        form.save()
        return super(ParticipantFormView, self).form_valid(form, *args, **kwargs)


class SurveyDispatchView(View):

    def dispatch(self, request, *args, **kwargs):
        participant = get_object_or_404(Participant.objects.select_related('survey'),
                                        password=self.kwargs['password'],
                                        pk=self.kwargs['participant'])
        dispatcher = {Survey.STYLE.total: ParticipantFormView,
                      Survey.STYLE.hospital: HospitalListView,
                      Survey.STYLE.question: QuestionListView}
        handler = dispatcher[participant.survey.style].as_view()
        return handler(request, *args, **kwargs)


class HospitalPrintView(HospitalListView):
    template_name = 'survey/survey_print.html'
    model = Hospital

    def get_form(self, hospital):
        return self.form_class(hospital=hospital,
                               participant=self.participant)

    def get_context_data(self, **kwargs):
        context = super(HospitalPrintView, self).get_context_data(**kwargs)
        context['hospital_forms'] = [SurveyHospitalForm(hospital=hospital,
                                                        form=self.get_form(hospital))
                                     for hospital in self.object_list]
        return context


class ParticipantPrintView(ParticipantMixin, TemplateView):
    template_name = 'survey/participant_print.html'
    model = Survey

    def get_context_data(self, **kwargs):
        context = super(ParticipantPrintView, self).get_context_data(**kwargs)
        context['participant_form'] = ParticipantForm(participant=self.participant,
                                                      user=self.request.user)
        return context


class SurveyPrintDispatchView(View):

    def dispatch(self, request, *args, **kwargs):
        participant = get_object_or_404(Participant.objects.select_related('survey'),
                                        password=self.kwargs['password'],
                                        pk=self.kwargs['participant'])
        dispatcher = {Survey.PRINT_STYLE.per_hospital: HospitalPrintView,
                      Survey.PRINT_STYLE.per_participant: ParticipantPrintView}
        handler = dispatcher[participant.survey.print_style].as_view(cached_participant=participant)
        return handler(request, *args, **kwargs)
