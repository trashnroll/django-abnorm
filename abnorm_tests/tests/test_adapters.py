from django.test import TestCase

from .models import (
    TestObj,
    GenericRelatedTestObj,
    M2MTestObj,
    NonOrderedModel,
)
from abnorm.adapters import this_django


class DjangoAdapterTestCase(TestCase):

    def test_get_descriptor_rel_model(self):
        # ManyToManyDescriptor case
        self.assertEqual(
            this_django.get_descriptor_rel_model(
                GenericRelatedTestObj.m2m_items),
            M2MTestObj
        )

        # the same with reverse descriptor
        self.assertEqual(
            this_django.get_descriptor_rel_model(
                M2MTestObj.testobj_set),
            TestObj
        )

        # ReverseGenericRelatedObjectsDescriptor case
        self.assertEqual(
            this_django.get_descriptor_rel_model(TestObj.grto_items),
            GenericRelatedTestObj
        )

        # ForeignRelatedObjectsDescriptor case
        self.assertEqual(
            this_django.get_descriptor_rel_model(TestObj.non_ordereds),
            NonOrderedModel
        )

    def test_get_descriptor_remote_field(self):
        # ManyToManyDescriptor case
        self.assertEqual(
            this_django.get_descriptor_remote_field(
                TestObj.m2m_items),
            M2MTestObj.testobj_set.field
        )

        # the same with reverse descriptor
        self.assertEqual(
            this_django.get_descriptor_remote_field(
                M2MTestObj.testobj_set),
            TestObj.m2m_items.field
        )

        # ReverseGenericRelatedObjectsDescriptor case
        self.assertEqual(
            this_django.get_descriptor_remote_field(
                TestObj.m2m_items),
            M2MTestObj.testobj_set.field
        )

        # ForeignRelatedObjectsDescriptor case
        self.assertEqual(
            this_django.get_descriptor_remote_field(TestObj.non_ordereds),
            NonOrderedModel.test_obj.field
        )
