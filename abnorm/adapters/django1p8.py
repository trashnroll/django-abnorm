from funcy import first

from .django1p7 import SpecificDjango as Django1p7


class SpecificDjango(Django1p7):
    def get_descriptor_rel_model(self, descriptor):
        remote_field = self.get_descriptor_remote_field(descriptor)
        if isinstance(descriptor, self.ManyToManyDescriptor):
            return remote_field.related_model
        elif isinstance(descriptor, self.ForeignRelatedObjectsDescriptor):
            return remote_field.model
        elif isinstance(descriptor,
                        self.ReverseGenericRelatedObjectsDescriptor):
            return remote_field.rel.to
        raise Exception(
            'dont know how to deal with descriptor of type %s' % descriptor)

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
                def to(self):
                    if hasattr(field, 'model'):
                        descriptor = getattr(
                            field.model, field.relation_name, None)
                        if descriptor:
                            return this_django.get_descriptor_rel_model(
                                descriptor)

                # see ForeignObjectRel.model property implementation,
                # introduced in django 1.8
                model = to

            field.rel = Rel()

    def add_subfield_base_metaclass(self, cls):
        # just do nothing, as SubfieldBase is deprecated in favor of
        # from_db_value since django 1.8
        return cls

    def get_field_backwards_name(self, field):
        descriptor = getattr(field.model, field.relation_name)
        rf = self.get_descriptor_remote_field(descriptor)
        from django.db.models.fields.related import (
            ForeignKey, ManyToManyField)
        from django.contrib.contenttypes.fields import GenericRelation
        if isinstance(rf, ForeignKey):
            return rf.name
        elif isinstance(rf, ManyToManyField):
            return rf.related.get_accessor_name()
        elif isinstance(rf, GenericRelation):
            return first([
                f for f in self.get_model_fields(
                    descriptor.field.related_model)
                if self._is_matching_generic_foreign_key(descriptor.field, f)
            ]).name

    def get_model_fields(self, model):
        return model._meta.get_fields(include_hidden=True)
