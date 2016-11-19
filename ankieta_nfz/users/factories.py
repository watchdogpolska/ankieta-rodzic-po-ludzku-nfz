import factory
from . import models


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'user%d' % n)
    email = factory.LazyAttribute(lambda obj: '%s@example.com' % obj.username)
    password = factory.PostGenerationMethodCall('set_password', 'pass')

    class Meta:
        model = models.User
        django_get_or_create = ('username', )
