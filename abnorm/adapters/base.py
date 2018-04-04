
def _patch_descriptor_backwards_relation(descriptor):
    # we need to patch backwards relation for nullable fields to override
    # related_manager_cls.remove and related_manager_cls.clear methods
    # since they are using update orm technique w/o having any signal
    # see django.db.models.fields.related.ForeignRelatedObjectsDescriptor
    # (django 1.6-1.8) or
    # django.db.models.fields.related_descriptors.ReverseManyToOneDescriptor
    # (django 1.9+) related_manager_cls property for details

    _remove_orig = descriptor.related_manager_cls.remove
    _clear_orig = descriptor.related_manager_cls.clear

    def remove(self, *objs, **kwargs):
        result = _remove_orig(self, *objs, **kwargs)
        for field in descriptor._abnorm_slave_fields:
            field.update_value(self.instance)
        return result
    remove.alters_data = True
    remove._wrapped = _remove_orig

    def clear(self):
        result = _clear_orig(self)
        for field in descriptor._abnorm_slave_fields:
            field.update_value(self.instance)
        return result
    clear.alters_data = True
    clear._wrapped = _clear_orig

    descriptor.related_manager_cls.remove = remove
    descriptor.related_manager_cls.clear = clear


def _patch_foreign_related_object_descriptor_once(descriptor):
    if not hasattr(descriptor, '_abnorm_slave_fields'):
        descriptor._abnorm_slave_fields = []
        _patch_descriptor_backwards_relation(descriptor)


class EveryDjango(object):

    def perform_delayed_setup_signals(self, sender, **kwargs):
        from .. import state
        while state.delayed_setup_signals:
            model, field = state.delayed_setup_signals.pop()
            field.setup_signals(model)

    def add_foreign_related_object_descriptor_slave_field(
            self, descriptor, field):
        _patch_foreign_related_object_descriptor_once(descriptor)
        descriptor._abnorm_slave_fields.append(field)
