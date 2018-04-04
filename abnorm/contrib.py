from django.db import models
from django.contrib.postgres.fields import ArrayField

from .fields import DenormalizedFieldMixin


class RelationValueSetField(DenormalizedFieldMixin, ArrayField):

    def __init__(self, *args, **kwargs):
        self.field_name = kwargs.pop('field_name', None)
        kwargs.setdefault('base_field', models.IntegerField())
        super(RelationValueSetField, self).__init__(*args, **kwargs)

    def get_denormalized_value(self, instance=None, relation=None):
        queryset = self.get_related_queryset(instance, relation)
        # can't tell django to avoid outer join, so have to explicitly handle
        # empty relations case: drop `field` for `foos__bars__field` and
        # exclude null values
        relation = '__'.join(self.field_name.split('__')[:-1])
        if relation:
            queryset = queryset.exclude(**{relation: None})

        values = queryset.values_list(self.field_name, flat=True)
        return list(set(values))

    def deconstruct(self):
        # django 1.7+
        name, path, args, kwargs = super(
            RelationValueSetField, self).deconstruct()
        kwargs['field_name'] = self.field_name
        return name, path, args, kwargs
