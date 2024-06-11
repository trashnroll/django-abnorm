from django.utils.module_loading import import_string
from django import VERSION as DJANGO_VERSION

SUPPORTED_DJANGO_VERSIONS = [
    (2, 2),
    (3, 0),
    (3, 1),
    (3, 2),
    (4, 0),
    (4, 1),
    (4, 2),
]

if DJANGO_VERSION[:2] not in SUPPORTED_DJANGO_VERSIONS:
    raise NotImplementedError(
        'No working version for django %s.%s yet. Welcome to the land of '
        'opportunities!' % DJANGO_VERSION[:2]
    )


SpecificDjango = import_string(
    'abnorm.adapters.django%sp%s.SpecificDjango' % DJANGO_VERSION[:2])

this_django = SpecificDjango()
