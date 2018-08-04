import sys

from importlib import import_module

from django.utils import six
from django import VERSION as DJANGO_VERSION

SUPPORTED_DJANGO_VERSIONS = [
    (1, 6),
    (1, 7),
    (1, 8),
    (1, 9),
    (1, 10),
    (1, 11),
    (2, 0),
    (2, 1),
]

if DJANGO_VERSION[:2] not in SUPPORTED_DJANGO_VERSIONS:
    raise NotImplementedError(
        'No working version for django %s.%s yet. Welcome to the land of '
        'opportunities!' % DJANGO_VERSION[:2]
    )


# copy-pasted from django 1.7 sources to support django 1.6
def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by
    the last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])


SpecificDjango = import_string(
    'abnorm.adapters.django%sp%s.SpecificDjango' % DJANGO_VERSION[:2])

this_django = SpecificDjango()
