from django.test import TestCase
from django.core.management import call_command

from .models import (
    TestObj, RelatedTestObj, NullRelatedTestObj, GenericRelatedTestObj,
    M2MTestObj, TestParentObj
)

from abnorm.utils import reload_model_instance


class UpdateFieldsCommandTestCase(TestCase):
    def setUp(self):
        self.test_parent_obj = TestParentObj.objects.create()
        self.test_obj = TestObj.objects.create(parent=self.test_parent_obj)

        # M2M
        self.m2m = M2MTestObj.objects.create(value=0)
        self.test_obj.m2m_items.add(self.m2m)

        # foreign keys
        self.rto = RelatedTestObj.objects.create(
            test_obj=self.test_obj, value=0)
        self.grto = GenericRelatedTestObj.objects.create(
            content_object=self.test_obj, value=0)
        self.nrto = NullRelatedTestObj.objects.create(
            test_obj=self.test_obj, value=0)

        # reload objects
        self.test_obj = reload_model_instance(self.test_obj)
        self.test_parent_obj = reload_model_instance(self.test_parent_obj)

    def test_updates_relation_fields(self):
        for relation in ('rto', 'grto', 'nrto', 'm2m'):
            obj = getattr(self, relation)

            # lets update data in our db with signal-free update statement
            # to suppress normal abnorm behavior
            type(obj).objects.filter(pk=obj.pk).update(value=999)

            # make sure denormalized field value was not updated
            self.test_obj = reload_model_instance(self.test_obj)

            denormed_obj = getattr(self.test_obj, relation + '_first_item')
            self.assertEqual(denormed_obj.value, 0)

            # run update fields command
            call_command(
                'update_abnorm_fields',
                'abnorm.TestObj.{}_first_item'.format(relation),
            )

            # ensure our data is updated
            self.test_obj = reload_model_instance(self.test_obj)
            denormed_obj = getattr(self.test_obj, relation + '_first_item')
            self.assertEqual(denormed_obj.value, 999)

    def test_uses_post_update_signal(self):
        # lets update data in our db with signal-free update statement
        # to suppress normal abnorm behavior
        type(self.m2m).objects.filter(pk=self.m2m.pk).update(value=999)

        # run update fields command
        call_command(
            'update_abnorm_fields',
            'abnorm.TestObj.m2m_first_item',
        )

        # post_update signal fired
        self.test_parent_obj = reload_model_instance(self.test_parent_obj)
        denormed_obj = self.test_parent_obj.first_test_obj.m2m_first_item
        self.assertEqual(denormed_obj.value, 999)

    def test_updates_only_listed_fields(self):
        # abnorm is smart enough to update all instance's fields on save
        # unfortunately that creates heavy update queries

        # lets update data in our db with signal-free update statement
        # to suppress normal abnorm behavior
        type(self.rto).objects.filter(pk=self.rto.pk).update(value=999)
        type(self.grto).objects.filter(pk=self.grto.pk).update(value=999)
        type(self.nrto).objects.filter(pk=self.grto.pk).update(value=999)

        # this DOES NOT update nrto field
        call_command(
            'update_abnorm_fields',
            'abnorm.TestObj.rto_first_item',
            'abnorm.TestObj.grto_first_item',
        )

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_first_item.value, 999)
        self.assertEqual(self.test_obj.grto_first_item.value, 999)

        # nrto field was NOT updated
        self.assertNotEqual(self.test_obj.nrto_first_item.value, 999)
