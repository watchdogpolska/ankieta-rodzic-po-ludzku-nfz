from import_export import resources
from .models import NationalHealtFund, Hospital, Participant


class HospitalResource(resources.ModelResource):

    class Meta:
        model = Hospital


class NationalHealthFundResource(resources.ModelResource):

    class Meta:
        model = NationalHealtFund


class ParticipantResource(resources.ModelResource):

    class Meta:
        model = Participant
