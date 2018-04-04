from unittest import skipIf, skipUnless
import django
from django.test import TestCase

from .models import (
    TestObj, RelatedTestObj, NullRelatedTestObj, GenericRelatedTestObj,
    M2MTestObj, TestParentObj,
)

from abnorm.utils import reload_model_instance
from abnorm.adapters import this_django


class FKRelationTestCase(TestCase):
    def setUp(self):
        self.test_obj = TestObj.objects.create()
        self.test_obj2 = TestObj.objects.create()

        self.fm0 = RelatedTestObj.objects.create(
            value=0, test_obj=self.test_obj)
        self.fm1 = RelatedTestObj.objects.create(
            value=1, test_obj=self.test_obj)
        self.fm2 = RelatedTestObj.objects.create(
            value=2, test_obj=self.test_obj)
        self.fm3 = RelatedTestObj.objects.create(
            value=4, test_obj=self.test_obj)
        self.fm4 = RelatedTestObj.objects.create(
            value=8, test_obj=self.test_obj2)

        self.test_obj = reload_model_instance(self.test_obj)
        self.test_obj2 = reload_model_instance(self.test_obj2)

    def test_count_field(self):
        self.assertEqual(self.test_obj.rto_items_count, 4)
        self.assertEqual(self.test_obj2.rto_items_count, 1)

        self.fm4.test_obj = self.test_obj
        self.fm4.save()
        self.test_obj = reload_model_instance(self.test_obj)
        self.test_obj2 = reload_model_instance(self.test_obj2)
        self.assertEqual(self.test_obj.rto_items_count, 5)
        self.assertEqual(self.test_obj2.rto_items_count, 0)

    def test_count_field_with_qs_filter_value_change(self):
        self.fm5 = RelatedTestObj.objects.create(
            value=1, test_obj=self.test_obj)
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_qsf_count, 2)
        self.fm5.value = 666
        self.fm5.save()
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_qsf_count, 1)

    def test_count_field_with_qs_filter_both_val_and_relation_change(self):
        self.fm5 = RelatedTestObj.objects.create(
            value=1, test_obj=self.test_obj)

        self.fm5.test_obj = self.test_obj2
        self.fm5.save()

        self.test_obj = reload_model_instance(self.test_obj)
        self.test_obj2 = reload_model_instance(self.test_obj2)
        self.assertEqual(self.test_obj.rto_items_qsf_count, 1)
        self.assertEqual(self.test_obj2.rto_items_qsf_count, 1)

    def test_sum_field(self):
        self.assertEqual(self.test_obj.rto_item_values_sum, 7)

    def test_sum_field_for_relation_with_default_relation_name(self):
        RelatedTestObj.objects.create(
            value=17, test_obj_wo_related_name=self.test_obj,
            test_obj=self.test_obj)
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(
            self.test_obj.rto_with_default_related_name_item_values_sum, 17)

    def test_first_item_field(self):
        self.assertEqual(self.test_obj.rto_first_item, self.fm0)

    def test_first_2_items_field(self):
        self.assertEqual(self.test_obj.rto_first_2_items,
                         [self.fm0, self.fm1])

    def test_related_field_has_correct_fk_value(self):
        self.assertEqual(
            self.test_obj.rto_first_item.test_obj.pk, self.test_obj.pk)

    def test_altering_rto_first_item_attr_updates_itself(self):
        denormalized_item = self.test_obj.rto_first_item
        denormalized_item.value = 666
        self.assertEqual(denormalized_item.test_obj, self.test_obj)
        denormalized_item.save()  # just like if we got it from original model
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_first_item.value, 666)


class GenericRelationTestCase(TestCase):
    def setUp(self):
        self.test_obj = TestObj.objects.create()
        self.test_obj2 = TestObj.objects.create()

        self.fm0 = GenericRelatedTestObj.objects.create(
            value=0, content_object=self.test_obj)
        self.fm1 = GenericRelatedTestObj.objects.create(
            value=1, content_object=self.test_obj)
        self.fm2 = GenericRelatedTestObj.objects.create(
            value=2, content_object=self.test_obj)
        self.fm3 = GenericRelatedTestObj.objects.create(
            value=4, content_object=self.test_obj)
        self.fm4 = GenericRelatedTestObj.objects.create(
            value=8, content_object=self.test_obj2)

        self.test_obj = reload_model_instance(self.test_obj)
        self.test_obj2 = reload_model_instance(self.test_obj2)

    def test_count_field(self):
        self.assertEqual(self.test_obj.grto_items_count, 4)

    def test_sum_field(self):
        self.assertEqual(self.test_obj.grto_item_values_sum, 7)

    def test_first_item_field(self):
        self.assertEqual(self.test_obj.grto_first_item, self.fm0)

    def test_first_2_items_field(self):
        self.assertEqual(self.test_obj.grto_first_2_items,
                         [self.fm0, self.fm1])


class M2MRelationTestCase(TestCase):
    def setUp(self):
        self.test_obj = TestObj.objects.create()
        self.test_obj2 = TestObj.objects.create()

        self.fm0 = M2MTestObj.objects.create(value=0)
        self.fm1 = M2MTestObj.objects.create(value=1)
        self.fm2 = M2MTestObj.objects.create(value=2)
        self.fm3 = M2MTestObj.objects.create(value=4)
        self.fm4 = M2MTestObj.objects.create(value=8)
        self.fm_unused = M2MTestObj.objects.create(value=16)

        self.test_obj.m2m_items.add(self.fm0)
        self.test_obj.m2m_items.add(self.fm1)
        self.test_obj.m2m_items.add(self.fm2)
        self.test_obj.m2m_items.add(self.fm3)
        self.test_obj2.m2m_items.add(self.fm4)

        self.test_obj = reload_model_instance(self.test_obj)
        self.test_obj2 = reload_model_instance(self.test_obj2)

    def test_count_field(self):
        self.assertEqual(self.test_obj.m2m_items_count, 4)

    def test_sum_field(self):
        self.assertEqual(self.test_obj.m2m_item_values_sum, 7)

    def test_first_item_field(self):
        self.assertEqual(self.test_obj.m2m_first_item, self.fm0)

    def test_first_2_items_field(self):
        self.assertEqual(self.test_obj.m2m_first_2_items,
                         [self.fm0, self.fm1])


class PostUpdateTestCase(TestCase):
    def setUp(self):
        self.test_grand_parent = TestParentObj.objects.create()
        self.test_parent = TestParentObj.objects.create(
            parent=self.test_grand_parent)
        self.test_obj = TestObj.objects.create(parent=self.test_parent)

        self.fm0 = M2MTestObj.objects.create(value=0)
        self.fm1 = M2MTestObj.objects.create(value=1)

        self.test_obj.m2m_items.add(self.fm0)
        self.test_obj.m2m_items.add(self.fm1)

        self.test_grand_parent = reload_model_instance(self.test_grand_parent)
        self.test_parent = reload_model_instance(self.test_parent)
        self.test_obj = reload_model_instance(self.test_obj)

    def test_all_test_objs_field(self):
        # post_save fired
        self.assertEqual(self.test_parent.all_test_objs, [self.test_obj])

        # m2m fired
        self.assertEqual(self.test_obj.m2m_first_2_items, [self.fm0, self.fm1])

        # post_update fired
        self.assertEqual(self.test_parent.all_test_objs[0].m2m_first_2_items,
                         self.test_obj.m2m_first_2_items)

        # post_update fired up above
        self.assertEqual(self.test_grand_parent.all_children,
                         [self.test_parent])

        # Got abnormed data too
        self.assertEqual(
            (self.test_grand_parent.all_children[0]
             .all_test_objs[0].m2m_first_2_items),
            self.test_obj.m2m_first_2_items)

    def test_m2m_relation_updates_denorm_on_save(self):
        # prove initial data
        self.assertEqual(
            (self.test_grand_parent
             .all_children[0]
             .all_test_objs[0]
             .m2m_first_2_items[0]
             .value),
            0)

        # trigger update of m2m object
        self.fm0.value = 999
        self.fm0.save()

        # prove all date updated
        self.test_grand_parent = reload_model_instance(self.test_grand_parent)
        self.assertEqual(
            (self.test_grand_parent
             .all_children[0]
             .all_test_objs[0]
             .m2m_first_2_items[0].value),
            999)


class GRPostUpdateTestCase(TestCase):
    def setUp(self):
        self.test_obj = TestObj.objects.create()
        self.grto = GenericRelatedTestObj.objects.create(
            value=0, content_object=self.test_obj
        )

        self.m2m = M2MTestObj.objects.create(value=0)
        self.grto.m2m_items.add(self.m2m)
        self.grto = reload_model_instance(self.grto)
        self.test_obj = reload_model_instance(self.test_obj)

    def test_rto_post_update(self):
        # proves old value is 0
        self.assertEqual(
            self.test_obj.grto_first_item.m2m_first_item.value, 0)

        # trigger denormalized data update
        self.m2m.value = 999
        self.m2m.save()

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(
            self.test_obj.grto_first_item.m2m_first_item.value, 999)


class RTOCountDenormalizationTestCase(TestCase):
    def setUp(self):
        self.test_obj = TestObj.objects.create()
        self.another_test_obj = TestObj.objects.create()

    def test_zero_for_new_items(self):
        self.assertEqual(self.test_obj.rto_items_count, 0)

    def test_updated_after_replacing(self):
        RelatedTestObj.objects.create(value=0, test_obj=self.test_obj)
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_count, 1)

        self.test_obj.rto_items.create(value=1)
        self.test_obj.rto_items.create(value=2)
        self.test_obj.rto_items.create(value=3)

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_count, 4)

    @skipIf(django.VERSION >= (1, 9), 'django<1.9 feature')
    def test_updated_after_adding_pre_19(self):
        self.test_obj.rto_items.create(value=0)
        self.test_obj.rto_items.create(value=0)

        self.test_obj.rto_items.add(
            RelatedTestObj(value=0)
        )

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_count, 3)

    @skipUnless(django.VERSION >= (1, 9), 'django1.9+ feature')
    def test_updated_after_adding_since_19(self):
        self.test_obj.rto_items.create(value=0)
        self.test_obj.rto_items.create(value=0)

        self.test_obj.rto_items.add(
            RelatedTestObj(value=0), bulk=False
        )

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_count, 3)

    # no test_updated_after_removing as related manager for fk with null=False
    # has no 'remove' method

    def test_updated_after_clearing(self):
        self.test_obj.rto_items.create(value=0)
        self.test_obj.rto_items.create(value=0)

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_count, 2)

        this_django.m2m_set(self.test_obj, 'rto_items', [])

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_count, 2)

    def test_updated_after_adding_and_resaving(self):
        self.test_obj.rto_items.create(value=0)
        self.test_obj.rto_items.create(value=0)
        self.test_obj.save()

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_count, 2)

    def test_updated_after_changing_relation(self):
        rto = RelatedTestObj.objects.create(value=0, test_obj=self.test_obj)
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_count, 1)
        rto.test_obj = self.another_test_obj
        rto.save()
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_count, 0)
        self.another_test_obj = reload_model_instance(self.another_test_obj)
        self.assertEqual(self.another_test_obj.rto_items_count, 1)


class NullRTOCountDenormalizationTestCase(TestCase):
    def setUp(self):
        self.test_obj = TestObj.objects.create()
        self.another_test_obj = TestObj.objects.create()

    def test_zero_for_new_items(self):
        self.assertEqual(self.test_obj.nrto_items_count, 0)

    def test_updated_after_replacing(self):
        NullRelatedTestObj.objects.create(value=0, test_obj=self.test_obj)
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.nrto_items_count, 1)

        self.test_obj.rto_items.create(value=0)
        self.test_obj.rto_items.create(value=0)
        self.test_obj.rto_items.create(value=0)

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.rto_items_count, 3)

    def test_updated_after_adding(self):
        this_django.m2m_set(
            self.test_obj,
            'nrto_items',
            [
                NullRelatedTestObj.objects.create(
                    value=0, test_obj=self.test_obj),
                NullRelatedTestObj.objects.create(
                    value=0, test_obj=self.test_obj)
            ]
        )
        self.test_obj.nrto_items.add(
            NullRelatedTestObj.objects.create(value=0, test_obj=self.test_obj))

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.nrto_items_count, 3)

    def test_updated_after_removing(self):
        item1 = NullRelatedTestObj.objects.create(
            value=0, test_obj=self.test_obj)
        item2 = NullRelatedTestObj.objects.create(
            value=0, test_obj=self.test_obj)
        this_django.m2m_set(self.test_obj, 'nrto_items', [item1, item2])

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.nrto_items_count, 2)

        self.test_obj.nrto_items.remove(item1)

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.nrto_items_count, 1)

    def test_updated_after_clearing(self):
        self.test_obj.nrto_items.create(value=0)
        self.test_obj.nrto_items.create(value=0)

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.nrto_items_count, 2)

        this_django.m2m_set(self.test_obj, 'nrto_items', [])

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.nrto_items_count, 0)

    def test_updated_after_adding_and_resaving(self):
        self.test_obj.nrto_items.create(value=0)
        self.test_obj.nrto_items.create(value=0)

        self.test_obj.save()

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.nrto_items_count, 2)

    def test_updated_after_changing_relation(self):
        nrto = NullRelatedTestObj.objects.create(
            value=0, test_obj=self.test_obj)
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.nrto_items_count, 1)
        nrto.test_obj = self.another_test_obj
        nrto.save()
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.nrto_items_count, 0)
        self.another_test_obj = reload_model_instance(self.another_test_obj)
        self.assertEqual(self.another_test_obj.nrto_items_count, 1)


class GRTOCountDenormalizationTestCase(TestCase):
    def setUp(self):
        self.test_obj = TestObj.objects.create()
        self.another_test_obj = TestObj.objects.create()

    def test_zero_for_new_items(self):
        self.assertEqual(self.test_obj.grto_items_count, 0)

    def test_updated_after_replacing(self):
        this_django.m2m_set(
            self.test_obj,
            'grto_items',
            [
                GenericRelatedTestObj.objects.create(
                    value=0, content_object=self.test_obj),
                GenericRelatedTestObj.objects.create(
                    value=0, content_object=self.test_obj),
                GenericRelatedTestObj.objects.create(
                    value=0, content_object=self.test_obj),
            ]
        )

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.grto_items_count, 3)

    def test_updated_after_adding(self):
        this_django.m2m_set(
            self.test_obj,
            'grto_items',
            [
                GenericRelatedTestObj.objects.create(
                    value=0, content_object=self.test_obj),
                GenericRelatedTestObj.objects.create(
                    value=0, content_object=self.test_obj)
            ]
        )
        self.test_obj.grto_items.add(
            GenericRelatedTestObj.objects.create(
                value=0, content_object=self.test_obj)
        )

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.grto_items_count, 3)

    def test_updated_after_removing(self):
        grto1 = GenericRelatedTestObj.objects.create(
            value=0, content_object=self.test_obj)
        grto2 = GenericRelatedTestObj.objects.create(
            value=0, content_object=self.test_obj)
        this_django.m2m_set(self.test_obj, 'grto_items', [grto1, grto2])
        self.test_obj.grto_items.remove(grto1)

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.grto_items_count, 1)

    def test_updated_after_clearing(self):
        this_django.m2m_set(
            self.test_obj,
            'grto_items',
            [
                GenericRelatedTestObj.objects.create(
                    value=0, content_object=self.test_obj),
                GenericRelatedTestObj.objects.create(
                    value=0, content_object=self.test_obj)
            ]
        )
        this_django.m2m_set(self.test_obj, 'grto_items', [])

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.grto_items_count, 0)

    def test_updated_after_adding_and_resaving(self):
        grto1 = GenericRelatedTestObj.objects.create(
            value=0, content_object=self.test_obj)
        grto2 = GenericRelatedTestObj.objects.create(
            value=0, content_object=self.test_obj)
        this_django.m2m_set(self.test_obj, 'grto_items', [grto1, grto2])
        self.test_obj.save()

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.grto_items_count, 2)

    def test_updated_after_changing_relation(self):
        grto = GenericRelatedTestObj.objects.create(
            value=0, content_object=self.test_obj)
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.grto_items_count, 1)
        grto.content_object = self.another_test_obj
        grto.save()
        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.grto_items_count, 0)
        self.another_test_obj = reload_model_instance(self.another_test_obj)
        self.assertEqual(self.another_test_obj.grto_items_count, 1)


class M2MCountDenormalizationTestCase(TestCase):
    def setUp(self):
        self.test_obj = TestObj.objects.create()
        self.another_test_obj = TestObj.objects.create()

    def test_zero_for_new_items(self):
        self.assertEqual(self.test_obj.m2m_items_count, 0)

    def test_updated_after_replacing(self):
        this_django.m2m_set(
            self.test_obj,
            'm2m_items',
            [
                M2MTestObj.objects.create(value=0),
                M2MTestObj.objects.create(value=0),
                M2MTestObj.objects.create(value=0),
            ]
        )

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.m2m_items_count, 3)

    def test_updated_after_adding(self):
        this_django.m2m_set(
            self.test_obj,
            'm2m_items',
            [
                M2MTestObj.objects.create(value=0),
                M2MTestObj.objects.create(value=0),
            ]
        )
        self.test_obj.m2m_items.add(
            M2MTestObj.objects.create(value=0),
        )

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.m2m_items_count, 3)

    def test_updated_after_removing(self):
        m2m1 = M2MTestObj.objects.create(value=0)
        m2m2 = M2MTestObj.objects.create(value=0)

        this_django.m2m_set(
            self.test_obj,
            'm2m_items',
            [m2m1, m2m2]
        )
        self.test_obj.m2m_items.remove(m2m1)

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.m2m_items_count, 1)

    def test_updated_after_clearing(self):
        this_django.m2m_set(
            self.test_obj,
            'm2m_items',
            [
                M2MTestObj.objects.create(value=0),
                M2MTestObj.objects.create(value=0),
            ]
        )
        this_django.m2m_set(
            self.test_obj,
            'm2m_items',
            []
        )

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.m2m_items_count, 0)

    def test_updated_after_adding_and_resaving(self):
        m2m1 = M2MTestObj.objects.create(value=0)
        m2m2 = M2MTestObj.objects.create(value=0)
        this_django.m2m_set(
            self.test_obj,
            'm2m_items',
            [m2m1, m2m2]
        )
        self.test_obj.save()

        self.test_obj = reload_model_instance(self.test_obj)
        self.assertEqual(self.test_obj.m2m_items_count, 2)


class DropCascadeTestCase(TestCase):
    def setUp(self):
        self.parent = TestParentObj.objects.create()
        self.child = TestParentObj.objects.create(parent=self.parent)

    def test_doesnt_fail_on_broken_refs(self):
        # see DenormalizedFieldMixin.update_value_by try/except block comments
        self.parent.delete()
