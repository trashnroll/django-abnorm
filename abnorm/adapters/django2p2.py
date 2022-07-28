import sys

from django.apps import apps

from .base import EveryDjango


class SpecificDjango(EveryDjango):

    def __init__(self):
        self.hack_django_app_registry_once()

    def is_migration_command_running(self):
        command = (sys.argv[1:2] or [None])[0]
        return command in (
            'makemigrations',
            'migrate'
        )

    def hack_django_app_registry_once(self):
        from django.apps.registry import Apps
        this_django = self

        class AppsReadyDescriptor(object):
            def __init__(self, init_value=False):
                self.value = init_value

            def __get__(self, obj, objtype):
                return self.value

            def __set__(self, obj, value):
                self.value = value
                if value:
                    this_django.perform_delayed_setup_signals(None)

        Apps.ready = AppsReadyDescriptor(False)

    def get_relationfield_rel_model(self, field):
        descriptor = getattr(field.model, field.relation_name)
        return descriptor.field.model

    def get_descriptor_rel_model(self, descriptor):
        if isinstance(descriptor, self.ManyToManyDescriptor):
            if descriptor.reverse:
                return descriptor.field.model
            else:
                return descriptor.field.related_model
        elif isinstance(
                descriptor, self.ReverseGenericRelatedObjectsDescriptor):
            return descriptor.field.remote_field.model
        elif isinstance(descriptor, self.ForeignRelatedObjectsDescriptor):
            return descriptor.field.model
        raise Exception('dont know how to deal with descriptor of type %s'
                        % descriptor)

    def get_foreign_related_object_descriptor(self):
        from django.db.models.fields.related_descriptors import (
            ReverseManyToOneDescriptor)
        return ReverseManyToOneDescriptor

    ForeignRelatedObjectsDescriptor = property(
        get_foreign_related_object_descriptor)

    def get_descriptor_remote_field(self, descriptor):
        if isinstance(descriptor, self.ManyToManyDescriptor):
            return descriptor.field
        elif isinstance(descriptor, self.ForeignRelatedObjectsDescriptor):
            return descriptor.field
        elif isinstance(descriptor,
                        self.ReverseGenericRelatedObjectsDescriptor):
            return descriptor.field
        raise Exception(
            'dont know how to deal with descriptor of type %s' % descriptor)

    def get_reverse_generic_many_to_one_descriptor(self):
        from django.contrib.contenttypes.fields import (
            ReverseGenericManyToOneDescriptor)
        return ReverseGenericManyToOneDescriptor

    ReverseGenericRelatedObjectsDescriptor = property(
        get_reverse_generic_many_to_one_descriptor)

    def get_many_to_many_descriptor(self):
        from django.db.models.fields.related_descriptors import (
            ManyToManyDescriptor)
        return ManyToManyDescriptor

    ManyToManyDescriptor = property(get_many_to_many_descriptor)

    def apply_django_rel_hacks(self, field):
        if not self.is_migration_command_running():
            # see django.db.models.sql.compiler.SQLUpdateCompiler.as_sql
            # our val has prepare_database_save attr there, so the field
            # must have remote_field attr, otherwise we got TypeError
            field.db_constraint = False
            this_django = self

            class Rel(object):
                parent_link = None

                @property
                def model(self):
                    if hasattr(field, 'model'):
                        descriptor = getattr(
                            field.model, field.relation_name, None)
                        if descriptor:
                            return this_django.get_descriptor_rel_model(
                                descriptor)

            field.remote_field = Rel()

    def m2m_set(self, instance, relation_name, value):
        getattr(instance, relation_name).set(value)

    def get_field_backwards_name(self, field):
        descriptor = getattr(field.model, field.relation_name)
        rf = self.get_descriptor_remote_field(descriptor)
        from django.db.models.fields.related import (
            ForeignKey, ManyToManyField)
        from django.contrib.contenttypes.fields import GenericRelation
        if isinstance(rf, ForeignKey):
            return rf.name
        elif isinstance(rf, ManyToManyField):
            if descriptor.reverse:
                return rf.attname
            else:
                return rf.remote_field.get_accessor_name()
        elif isinstance(rf, GenericRelation):
            return [
                f for f in self.get_model_fields(
                    descriptor.field.related_model)
                if self._is_matching_generic_foreign_key(descriptor.field, f)
            ][0].name

    def _is_matching_generic_foreign_key(self, descriptor_field, field):
        """
        Return True if field is a GenericForeignKey whose content type and
        object id fields correspond to the equivalent attributes on this
        GenericRelation.
        """
        from django.contrib.contenttypes.fields import GenericForeignKey
        return (
            isinstance(field, GenericForeignKey) and
            field.ct_field == descriptor_field.content_type_field_name and
            field.fk_field == descriptor_field.object_id_field_name
        )

    def get_model(self, app_label, model_name=None):
        return apps.get_model(app_label, model_name)

    def get_model_fields(self, model):
        return model._meta.get_fields(include_hidden=True)
