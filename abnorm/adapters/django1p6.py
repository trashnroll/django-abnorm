import sys

from django.db import models
from django.db.models.loading import get_model
from django.contrib.contenttypes.generic import (
    ReverseGenericRelatedObjectsDescriptor)
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.contrib.contenttypes.generic import GenericRelation
from django.utils import six

from .base import EveryDjango


class SpecificDjango(EveryDjango):
    def get_relationfield_rel_model(self, field):
        descriptor = getattr(field.model, field.relation_name)
        if isinstance(
                descriptor,
                self.ReverseGenericRelatedObjectsDescriptor):
            return descriptor.field.rel.to
        elif isinstance(descriptor, self.ForeignRelatedObjectsDescriptor):
                return descriptor.related.field.model

    ReverseGenericRelatedObjectsDescriptor = (
        ReverseGenericRelatedObjectsDescriptor)

    def get_foreign_related_object_descriptor(self):
        from django.db.models.fields.related import (
            ForeignRelatedObjectsDescriptor)
        return ForeignRelatedObjectsDescriptor

    ForeignRelatedObjectsDescriptor = property(
        get_foreign_related_object_descriptor)

    def get_many_to_many_descriptor(self):
        from django.db.models.fields.related import (
            ReverseManyRelatedObjectsDescriptor)
        return ReverseManyRelatedObjectsDescriptor

    ManyToManyDescriptor = property(get_many_to_many_descriptor)

    def __init__(self):
        self.hack_django_app_cache_once()

    def is_migration_command_running(self):
        command = (sys.argv[1:2] or [None])[0]
        return command in (
            'schemamigration', 'datamigration', 'migrate'
        )

    def apply_django_rel_hacks(self, field):
        return

    def hack_django_app_cache_once(self):
        from django.db.models.loading import AppCache
        this_django = self

        class AppsCacheLoadedDescriptor(object):
            def __init__(self, init_value=False):
                self.value = init_value

            def __get__(self, obj, objtype):
                return self.value

            def __set__(self, obj, value):
                self.value = value
                if value:
                    this_django.perform_delayed_setup_signals(None)

        AppCache.loaded = AppsCacheLoadedDescriptor(False)

    def get_descriptor_remote_field(self, descriptor):
        if isinstance(descriptor, self.ManyToManyDescriptor):
            return descriptor.field
        elif isinstance(descriptor, self.ForeignRelatedObjectsDescriptor):
            return descriptor.related.field
        elif isinstance(descriptor,
                        self.ReverseGenericRelatedObjectsDescriptor):
            return descriptor.field
        raise Exception(
            'dont know how to deal with descriptor of type %s' % descriptor)

    def get_descriptor_rel_model(self, descriptor):
        remote_field = self.get_descriptor_remote_field(descriptor)
        if isinstance(descriptor, self.ManyToManyDescriptor):
            return remote_field.rel.to
        elif isinstance(descriptor, self.ForeignRelatedObjectsDescriptor):
            return remote_field.model
        elif isinstance(descriptor,
                        self.ReverseGenericRelatedObjectsDescriptor):
            return remote_field.rel.to
        raise Exception(
            'dont know how to deal with descriptor of type %s' % descriptor)

    def add_subfield_base_metaclass(self, cls):
        return six.add_metaclass(models.SubfieldBase)(cls)

    def _is_matching_generic_foreign_key(self, descriptor_field, field):
        """
        Return True if field is a GenericForeignKey whose content type and
        object id fields correspond to the equivalent attributes on this
        GenericRelation.
        """
        from django.contrib.contenttypes.generic import GenericForeignKey
        return (
            isinstance(field, GenericForeignKey) and
            field.ct_field == descriptor_field.content_type_field_name and
            field.fk_field == descriptor_field.object_id_field_name
        )

    def get_field_backwards_name(self, field):
        descriptor = getattr(field.model, field.relation_name)
        rf = self.get_descriptor_remote_field(descriptor)
        if isinstance(rf, ForeignKey):
            return rf.name
        elif isinstance(rf, ManyToManyField):
            return rf.related.get_accessor_name()
        elif isinstance(rf, GenericRelation):
            return [
                f for f in self.get_model_fields(descriptor.field.rel.to)
                if self._is_matching_generic_foreign_key(descriptor.field, f)
            ][0].name

    def get_model(self, app_label, model_name=None):
        if model_name is None:
            app_label, model_name = app_label.split('.')
        return get_model(app_label, model_name)

    def get_model_fields(self, model):
        return [
            model._meta.get_field_by_name(f)[0]
            for f in model._meta.get_all_field_names()
        ] + model._meta.virtual_fields

    def m2m_set(self, instance, relation_name, value):
        setattr(instance, relation_name, value)
