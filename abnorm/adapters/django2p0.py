from .django1p11 import SpecificDjango as Django1p11


class SpecificDjango(Django1p11):
    def get_descriptor_rel_model(self, descriptor):
        if isinstance(descriptor, self.ManyToManyDescriptor):
            return descriptor.field.related_model
        elif isinstance(
                descriptor, self.ReverseGenericRelatedObjectsDescriptor):
            return descriptor.field.remote_field.model
        elif isinstance(descriptor, self.ForeignRelatedObjectsDescriptor):
            return descriptor.field.model
        raise Exception('dont know how to deal with descriptor of type %s'
                        % descriptor)

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
