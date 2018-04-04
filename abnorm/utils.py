import json
from decimal import Decimal

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder


def reload_model_instance(instance):
    return type(instance)._base_manager.get(pk=instance.pk)


def get_model_name(model):
    return '%s.%s' % (model._meta.app_label, model._meta.object_name)


def dumps(value):
    return DjangoJSONEncoder().encode(value)


def loads(txt):
    value = json.loads(
        txt,
        parse_float=Decimal,
        encoding=settings.DEFAULT_CHARSET
    )
    return value
