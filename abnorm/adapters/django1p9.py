from funcy import first

from .django1p8 import SpecificDjango as Django1p8


class SpecificDjango(Django1p8):

    def get_relationfield_rel_model(self, field):
        descriptor = getattr(field.model, field.relation_name)
        return descriptor.field.model

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

    def get_descriptor_rel_model(self, descriptor):
        remote_field = self.get_descriptor_remote_field(descriptor)
        if isinstance(descriptor, self.ManyToManyDescriptor):
            return remote_field.related_model
        elif isinstance(
                descriptor, self.ReverseGenericRelatedObjectsDescriptor):
            return remote_field.rel.to
        elif isinstance(descriptor, self.ForeignRelatedObjectsDescriptor):
            return remote_field.model
        raise Exception(
            'dont know how to deal with descriptor of type %s' % descriptor)

    def get_foreign_related_object_descriptor(self):
        from django.db.models.fields.related_descriptors import (
            ReverseManyToOneDescriptor)
        return ReverseManyToOneDescriptor

    ForeignRelatedObjectsDescriptor = property(
        get_foreign_related_object_descriptor)

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
            import warnings
            from django.utils.deprecation import RemovedInDjango20Warning

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

                @property
                def to(self):
                    # keep django 1.9+ deprecation warnings
                    warnings.warn(
                        'Usage of ForeignObjectRel.to attribute has been '
                        'deprecated. Use the model attribute instead.',
                        RemovedInDjango20Warning, 2)
                    return self.model

            field.remote_field = Rel()

    def get_field_backwards_name(self, field):
        descriptor = getattr(field.model, field.relation_name)
        rf = self.get_descriptor_remote_field(descriptor)
        from django.db.models.fields.related import (
            ForeignKey, ManyToManyField)
        from django.contrib.contenttypes.fields import GenericRelation
        if isinstance(rf, ForeignKey):
            return rf.name
        elif isinstance(rf, ManyToManyField):
            return rf.remote_field.get_accessor_name()
        elif isinstance(rf, GenericRelation):
            return first([
                f for f in self.get_model_fields(
                    descriptor.field.related_model)
                if self._is_matching_generic_foreign_key(descriptor.field, f)
            ]).name
