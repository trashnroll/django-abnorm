import types

from functools import wraps, partial

import django
from django.db import models
from django.db.models import Sum, Avg
from django.db.models.fields.files import FieldFile
from django.db.models.signals import (
    pre_save, post_save, post_delete, post_init, m2m_changed, Signal)
from django.utils.functional import cached_property
from django.utils import six
from django.core.exceptions import ObjectDoesNotExist

from .adapters import this_django, south
from .utils import get_model_name, dumps, loads
from . import state


post_update = Signal(providing_args=['instance'])


def skippable(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if state.SKIP_SIGNALS:
            return
        return func(*args, **kwargs)
    return wrapper


def init_model(model, data):
    field_data = {}
    for f in model._meta.fields:
        if f.attname in data:
            field_data[f.attname] = f.to_python(data[f.attname])
    instance = model(**field_data)
    return instance


class DenormalizedFieldMixin(object):
    def __init__(self, relation_name=None, null=True, blank=True,
                 qs_filter=None, **kwargs):
        assert relation_name
        self.relation_name = relation_name
        self.filter = qs_filter or {}
        super(DenormalizedFieldMixin, self).__init__(
            null=null, blank=blank, **kwargs)

    @cached_property
    def backwards_name(self):
        return this_django.get_field_backwards_name(self)

    def deconstruct(self):
        # django 1.7+
        name, path, args, kwargs = super(
            DenormalizedFieldMixin, self).deconstruct()
        attr_names = ('relation_name',)
        for attr_name in attr_names:
            attr = getattr(self, attr_name)
            if attr:
                kwargs[attr_name] = attr
        return name, path, args, kwargs

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super(DenormalizedFieldMixin, self).contribute_to_class(
            cls, name, *args, **kwargs)
        if not self.model._meta.abstract and not state.SKIP_SIGNALS:
            if ((get_model_name(self.model), self.name)
                    not in state.signals_connected):
                state.delayed_setup_signals.append((cls, self))

    def get_denormalized_value(self, instance=None, relation=None):
        raise NotImplementedError('')

    def get_related_queryset(self, instance=None, relation=None):
        if relation is None:
            relation = getattr(instance, self.relation_name)
        return relation.filter(**self.filter)

    def patch_instance_prepare_database_save(self, sender, instance, **kwargs):
        # see `django.db.models.sql.compiler.SQLUpdateCompiler.as_sql` for
        # details
        if hasattr(instance, '_prepare_database_save'):
            return

        def prepare_database_save(self, field):
            if not isinstance(field, DenormalizedFieldMixin):
                return self._prepare_database_save(field)
            return field.get_prep_value(self)

        instance._prepare_database_save = instance.prepare_database_save
        instance.prepare_database_save = types.MethodType(
            prepare_database_save, instance)

    def connect_related_model_signals(self, model):
        post_init.connect(
            self.patch_instance_prepare_database_save, sender=model)
        pre_save.connect(self.related_model_pre_save, sender=model)
        post_save.connect(self.related_model_post_save, sender=model)
        post_delete.connect(self.related_model_post_delete, sender=model)

    def setup_signals(self, cls):
        if cls._meta.abstract:
            return

        pre_save.connect(self.augmented_model_pre_save, cls)

        descriptor = getattr(cls, self.relation_name)
        rel_model = this_django.get_descriptor_rel_model(descriptor)

        is_m2md = isinstance(descriptor, this_django.ManyToManyDescriptor)
        is_frod = isinstance(
            descriptor, this_django.ForeignRelatedObjectsDescriptor)
        is_grod = isinstance(
            descriptor, this_django.ReverseGenericRelatedObjectsDescriptor)

        descriptor_field = this_django.get_descriptor_remote_field(descriptor)
        if is_m2md:
            post_init.connect(
                self.patch_instance_prepare_database_save, sender=rel_model)
            m2m_changed.connect(self.m2m_changed, sender=descriptor.through)
        elif is_frod:
            # patch nullable FK and One2One fields
            #: see AbnormForeignRelatedObjectsDescriptor comments
            if descriptor_field.null:
                this_django.add_foreign_related_object_descriptor_slave_field(
                    descriptor, self)
                setattr(cls, self.relation_name, descriptor)

        # post_update signal machinery below
        if is_grod:
            # get GenericForeignKey field name, which is customizable
            generic_fk_fields = filter(
                partial(
                    this_django._is_matching_generic_foreign_key,
                    descriptor_field
                ),
                this_django.get_model_fields(rel_model)
            )
            related_field = next(iter(generic_fk_fields), None)
            related_field_name = getattr(related_field, 'name', None)
        else:
            related_field_name = descriptor_field.name

        if related_field_name and related_field_name != '+':
            # if backwards relation name is not disabled, sign current
            # instance to update *current* field parent, see
            # https://docs.djangoproject.com/en/stable/ref/models/fields/
            # #django.db.models.ForeignKey.related_name
            # for details
            receiver = self.get_post_update_receiver(related_field_name)

            # local functions are garbage collected, so disable weak refs
            post_update.connect(receiver, sender=rel_model, weak=False)

        if django.VERSION < (1, 9) or (is_frod or is_m2md):
            # required for all descriptor types with django 1.6-1.8 for some
            # reason, and only for (is_frod or is_m2md) case with 1.9+
            self.connect_related_model_signals(rel_model)

        state.signals_connected.append((get_model_name(self.model), self.name))

    @skippable
    def augmented_model_pre_save(self, sender, instance, **kwargs):
        if instance.pk:
            setattr(instance, self.name, self.get_denormalized_value(instance))

    @skippable
    def related_model_pre_save(self, sender, instance, raw=False, using=None,
                               update_fields=None, **kwargs):
        # need original field value to track changed relations
        db_instance = type(instance)._base_manager.filter(
            pk=instance.pk).first()
        if db_instance:
            prev_value = getattr(db_instance, self.backwards_name)
            setattr(instance, '_%s_prev' % self.backwards_name, prev_value)

    @skippable
    def related_model_post_save(self, sender, instance, created, raw=False,
                                using=None, update_fields=None, **kwargs):
        # TODO: consider update_fields value
        self.update_value_by(instance)

    @skippable
    def related_model_post_delete(self, sender, instance, **kwargs):
        self.update_value_by(instance)

    @skippable
    def m2m_changed(self, sender, instance, action, reverse=False,
                    model=None, pk_set=None, using=None, **kwargs):
        if action in ('post_add', 'post_remove', 'post_clear'):
            self.update_value(instance)

    def get_post_update_receiver(self, related_field):
        @skippable
        def post_update_receiver(sender, instance, **kwargs):
            related_instance = getattr(instance, related_field)
            if related_instance is not None:
                self.update_value(related_instance)

        return post_update_receiver

    def update_value_by(self, related_instance):
        try:
            augmented_instance = getattr(
                related_instance, self.backwards_name, None)
        except ObjectDoesNotExist:
            # In order to make signals work as expected for cascade deletes
            # django instantiates all involved objects and deletes them
            # one by one.
            # During this process some objects may eventually possess broken
            # refs (e.g. foreing keys) to another affected records, which are
            # already deleted and, therefore, considered not existing within
            # current transaction.
            # Have nothing to do with such broken refs, just exit.
            return

        instances = (
            augmented_instance.all()
            if isinstance(augmented_instance, models.Manager)
            else [augmented_instance]
        )

        for instance in instances:
            self.update_value(instance)

    def update_value(self, augmented_instance):
        if not isinstance(augmented_instance, self.model):
            return
        value = self.get_prep_value(
            self.get_denormalized_value(augmented_instance))
        augmented_model = augmented_instance._meta.model
        augmented_model.objects.filter(pk=augmented_instance.pk).update(
            **{self.name: value})

        # inform related models it's been updated
        post_update.send(
            sender=type(augmented_instance),
            instance=augmented_instance,
        )


class AggregateField(DenormalizedFieldMixin):
    # this class just overrides default value of constructor `default` kwarg
    def __init__(self, relation_name=None, internal_type=None, default=0,
                 **kwargs):
        return super(AggregateField, self).__init__(
            relation_name=relation_name, default=default, **kwargs)


@this_django.add_subfield_base_metaclass
class CountField(AggregateField, models.IntegerField):

    def get_denormalized_value(self, instance=None, relation=None):
        return self.get_related_queryset(instance, relation).count()

    @skippable
    def related_model_post_save(self, sender, instance, created, raw=False,
                                using=None, update_fields=None, **kwargs):
        if created:
            self.update_value_by(instance)
        else:
            current_val = getattr(instance, self.backwards_name)
            prev_val = getattr(
                instance, '_%s_prev' % self.backwards_name, None)
            if prev_val != current_val or self.filter:
                # there's a room for optimization here, we can check if
                # `qs_filter` affected fields were actually changed

                #: relation changed case
                if prev_val != current_val and prev_val:
                    self.update_value(prev_val)
                self.update_value_by(instance)


class AnnotateField(AggregateField):
    def __init__(self, relation_name, field_name, **kwargs):
        super(AnnotateField, self).__init__(
            relation_name=relation_name, **kwargs)
        self.field_name = field_name

    def deconstruct(self):
        # django 1.7+
        name, path, args, kwargs = super(
            DenormalizedFieldMixin, self).deconstruct()
        attr_names = ('relation_name', 'field_name', 'internal_type')
        for attr_name in attr_names:
            attr = getattr(self, attr_name)
            if attr:
                kwargs[attr_name] = attr
        return name, path, args, kwargs

    @skippable
    def related_model_post_save(self, sender, instance, created, raw=False,
                                using=None, update_fields=None, **kwargs):
        self.update_value_by(instance)


class GenericSumField(AnnotateField):
    def get_denormalized_value(self, instance=None, relation=None):
        qs = self.get_related_queryset(instance, relation)
        result_key = '%s__sum' % self.field_name
        result = qs.aggregate(Sum(self.field_name))
        value = result[result_key]
        return value if value is not None else self.default


class SumField(object):
    def __new__(cls, *args, **kwargs):
        internal_type = kwargs.pop('internal_type', models.IntegerField)
        field_class = this_django.add_subfield_base_metaclass(
            type(
                'SumField', (GenericSumField, internal_type),
                {'internal_type': internal_type}
            )
        )
        return field_class(*args, **kwargs)


class GenericAvgField(AnnotateField):
    def get_denormalized_value(self, instance=None, relation=None):
        qs = self.get_related_queryset(instance, relation)
        result_key = '%s__avg' % self.field_name
        result = qs.aggregate(Avg(self.field_name))
        value = result[result_key]
        return value if value is not None else self.default


class AvgField(object):
    def __new__(cls, *args, **kwargs):
        internal_type = kwargs.pop('internal_type', models.FloatField)
        field_class = this_django.add_subfield_base_metaclass(
            type(
                'AvgField', (GenericAvgField, internal_type),
                {'internal_type': internal_type}
            )
        )
        return field_class(*args, **kwargs)


@this_django.add_subfield_base_metaclass
class RelationField(DenormalizedFieldMixin, models.TextField):

    generate_reverse_relation = False

    def __init__(self, relation_name=None, fields=None, limit=0,
                 flat=False, **kwargs):
        if not fields:
            raise ValueError('fields is a required parameter')
        for field in fields:
            assert '__' not in field
        self.fields = fields
        self.limit = limit
        self.flat = flat
        kwargs['default'] = (
            kwargs.get('default') or (None if limit == 1 and flat else []))
        super(RelationField, self).__init__(
            relation_name=relation_name, **kwargs)

        this_django.apply_django_rel_hacks(self)
        self.to_fields = [None]

    def deconstruct(self):
        # django 1.7+
        name, path, args, kwargs = super(
            DenormalizedFieldMixin, self).deconstruct()
        attr_names = ('fields', 'relation_name', 'limit', 'flat',)
        for attr_name in attr_names:
            attr = getattr(self, attr_name)
            if attr:
                kwargs[attr_name] = attr
        return name, path, args, kwargs

    def extract_item_fields(self, item):
        result = {}
        for field_name in self.fields:
            result[field_name] = self.extract_item_field(item, field_name)
        return result

    def extract_item_field(self, item, field_name):
        field_value = getattr(item, field_name)
        if isinstance(field_value, FieldFile):
            field_value = field_value.name
        elif isinstance(field_value, (models.Model, list)) and field_value:
            remote_field = this_django.get_relationfield_rel_model(
                self)._meta.get_field(field_name)

            if isinstance(remote_field, DenormalizedFieldMixin):
                field_value = loads(remote_field.serialize_value(field_value))

        return field_value

    def get_denormalized_value(self, instance=None, relation=None):
        qs = self.get_related_queryset(instance, relation)
        if self.limit == 1 and self.flat:
            return qs.first()
        elif self.limit:
            qs = qs[:self.limit]
        return list(qs)

    def to_python(self, value):
        if state.SKIP_SIGNALS:
            return value
        return self.deserialize_value(value)

    def deserialize_value(self, value):
        if value is None or value == '':
            return None

        descriptor = getattr(self.model, self.relation_name)
        model = this_django.get_descriptor_rel_model(descriptor)

        if isinstance(value, six.string_types):
            value = loads(value)

        if self.limit == 1 and self.flat:
            if not isinstance(value, dict):
                value = self.extract_item_fields(value)
            return init_model(model, value)

        elif isinstance(value, list):
            not_list_of_dicts = any(
                map(lambda item: not isinstance(item, dict), value))

            if not_list_of_dicts:
                value = [self.extract_item_fields(v) for v in value]

            return [init_model(model, v) for v in value]
        return value

    def get_prep_value(self, value):
        if state.SKIP_SIGNALS:
            return value
        return self.serialize_value(value)

    def from_db_value(self, value, expression, connection, context):
        # a reverse of `get_prep_value` since django 1.8
        return self.to_python(value)

    def serialize_value(self, value):
        if isinstance(value, models.query.QuerySet):
            value = list(value)

        if value is None:
            value = ''
        elif not isinstance(value, six.string_types):
            if self.limit == 1 and self.flat:
                value = self.extract_item_fields(value)
            else:
                value = [self.extract_item_fields(v) for v in value]
            value = dumps(value)

        return value


south.setup_rules()
