from collections import namedtuple

from braces.views import FormValidMessageMixin
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.views.generic import FormView, ListView

from .forms import SurveyForm
from .models import Hospital, Participant

LinkedHospital = namedtuple('LinkedHospital', ['obj', 'link'])


class HospitalListView(ListView):
    model = Hospital
    template_name = 'survey/hospital_list.html'

    def get_queryset(self, *args, **kwargs):
        qs = super(HospitalListView, self).get_queryset(*args, **kwargs)
        qs = qs.filter(health_fund__participant__password=self.kwargs['password'],
                       health_fund__participant=self.kwargs['participant']).all()
        return qs

    def get_context_data(self, **kwargs):
        context = super(HospitalListView, self).get_context_data(**kwargs)
        linked_hospitals = []
        for hospital in self.object_list:
            link = reverse('survey:survey', kwargs={'password': self.kwargs['password'],
                                                    'participant': self.kwargs['participant'],
                                                    'hospital': hospital.pk})
            linked_hospitals.append(LinkedHospital(hospital, link))
        context['linked_hospitals'] = linked_hospitals
        return context


class HospitalSurveyView(FormValidMessageMixin, FormView):
    form_class = SurveyForm
    template_name = 'survey/hospital_form.html'

    @cached_property
    def participant(self):
        return get_object_or_404(Participant,
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
        kw['survey'] = self.survey
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
