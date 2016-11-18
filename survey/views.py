from collections import namedtuple

from braces.views import FormValidMessageMixin
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.views.generic import FormView, ListView

from .forms import SurveyForm
from .models import Hospital, Participant

LinkedHospital = namedtuple('LinkedHospital', ['obj', 'link', 'status'])

SurveyHospitalForm = namedtuple('SurveyHospitalForm', ['hospital', 'form'])


class HospitalMixin(object):
    model = Hospital

    def get_queryset(self, *args, **kwargs):
        qs = super(HospitalMixin, self).get_queryset(*args, **kwargs)
        qs = qs.filter(health_fund__participant__password=self.kwargs['password'],
                       health_fund__participant=self.kwargs['participant']).all()
        qs = qs.answer_fetch(self.kwargs['participant'])
        return qs


class HospitalListView(HospitalMixin, ListView):
    model = Hospital
    template_name = 'survey/hospital_list.html'

    def get_context_data(self, **kwargs):
        context = super(HospitalListView, self).get_context_data(**kwargs)
        linked_hospitals = []
        for hospital in self.object_list:
            link = reverse('survey:survey', kwargs={'password': self.kwargs['password'],
                                                    'participant': self.kwargs['participant'],
                                                    'hospital': hospital.pk})
            linked = LinkedHospital(obj=hospital,
                                    link=link,
                                    status=len(hospital.answer_participant) > 0)
            linked_hospitals.append(linked)
        context['linked_hospitals'] = linked_hospitals
        context['print_url'] = reverse('survey:print', kwargs={'password': self.kwargs['password'],
                                                               'participant': self.kwargs['participant']})
        return context


class SurveyPrintView(HospitalListView):
    template_name = 'survey/survey_print.html'
    form_class = SurveyForm
    model = Hospital

    @cached_property
    def participant(self):
        return get_object_or_404(Participant.objects.with_survey(),
                                 password=self.kwargs['password'],
                                 pk=self.kwargs['participant'])

    def get_form(self, hospital):
        return self.form_class(hospital=hospital,
                               participant=self.participant)

    def get_context_data(self, **kwargs):
        context = super(SurveyPrintView, self).get_context_data(**kwargs)
        hospital_forms = []
        for hospital in self.object_list:
            linked = SurveyHospitalForm(hospital=hospital,
                                        form=self.get_form(hospital))
            hospital_forms.append(linked)
        context['hospital_forms'] = hospital_forms
        return context


class HospitalSurveyView(FormValidMessageMixin, FormView):
    form_class = SurveyForm
    template_name = 'survey/hospital_form.html'

    @cached_property
    def participant(self):
        return get_object_or_404(Participant.objects.with_survey(),
                                 password=self.kwargs['password'],
                                 pk=self.kwargs['participant'])

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
        return kw

    def get_context_data(self, **kwargs):
        context = super(HospitalSurveyView, self).get_context_data(**kwargs)
        context['survey'] = self.survey
        context['hospital'] = self.hospital
        return context

    def get_success_url(self):
        return reverse('survey:list', kwargs={'password': self.kwargs['password'],
                                              'participant': self.kwargs['participant']})

    def get_form_valid_message(self):
        return _("Answer for {hospital} was saved!").format(hospital=self.hospital)

    def form_valid(self, form, *args, **kwargs):
        form.save()
        return super(HospitalSurveyView, self).form_valid(form, *args, **kwargs)
