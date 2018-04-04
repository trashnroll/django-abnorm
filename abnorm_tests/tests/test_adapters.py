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
