from django.db import models
from django.contrib.contenttypes.models import ContentType
from django import VERSION as DJANGO_VERSION

from abnorm import SumField, CountField, RelationField

if DJANGO_VERSION < (1, 8):
    from django.contrib.contenttypes import generic
else:
    from django.contrib.contenttypes import fields as generic


class BaseModel(models.Model):
    class Meta:
        abstract = True

    def __str__(self):
        return '{} #{}'.format(self.__class__.__name__, self.pk)

    # Py2 compatibility
    __unicode__ = __str__


class TestParentObj(BaseModel):
    parent = models.ForeignKey(
        'self', null=True, related_name='children', on_delete=models.CASCADE)
    all_test_objs = RelationField(
        'test_objs', fields=('id', 'm2m_first_2_items'))
    all_children = RelationField('children', fields=('id', 'all_test_objs'))
    first_test_obj = RelationField(
        'test_objs', fields=('id', 'm2m_first_2_items', 'm2m_first_item'),
        limit=1, flat=True)

    class Meta:
        app_label = 'abnorm'


class TestObj(BaseModel):
    parent = models.ForeignKey(
        TestParentObj, null=True, related_name='test_objs',
        on_delete=models.CASCADE)
    rto_item_values_sum = SumField('rto_items', 'value')
    rto_with_default_related_name_item_values_sum = SumField(
        'relatedtestobj_set', 'value')
    rto_items_count = CountField('rto_items')
    rto_items_qsf_count = CountField('rto_items', qs_filter={'value': 1})
    rto_first_item = RelationField(
        'rto_items', fields=('id', 'value', 'test_obj_id'), limit=1, flat=True)
    rto_first_2_items = RelationField(
        'rto_items', fields=('id', 'value'), limit=2)

    nrto_item_values_sum = SumField('nrto_items', 'value')
    nrto_items_count = CountField('nrto_items')
    nrto_first_item = RelationField(
        'nrto_items', fields=('id', 'value'), limit=1, flat=True)
    nrto_first_2_items = RelationField(
        'nrto_items', fields=('id', 'value'), limit=2)

    grto_items = generic.GenericRelation('abnorm.GenericRelatedTestObj')
    grto_item_values_sum = SumField('grto_items', 'value')
    grto_items_count = CountField('grto_items')
    grto_first_item = RelationField(
        'grto_items', fields=('id', 'value', 'm2m_first_item'), limit=1,
        flat=True)
    grto_first_2_items = RelationField(
        'grto_items', fields=('id', 'value'), limit=2)

    m2m_items = models.ManyToManyField('M2MTestObj')
    m2m_item_values_sum = SumField('m2m_items', 'value')
    m2m_items_count = CountField('m2m_items')
    m2m_first_item = RelationField(
        'm2m_items', fields=('id', 'value'), limit=1, flat=True)
    m2m_first_2_items = RelationField(
        'm2m_items', fields=('id', 'value'), limit=2)
    first_non_ordered = RelationField(
        'non_ordereds', fields=('id', 'value'), limit=1, flat=True)

    class Meta:
        app_label = 'abnorm'


class NonOrderedModel(BaseModel):

    value = models.IntegerField(default=0)
    test_obj = models.ForeignKey(
        TestObj, related_name='non_ordereds', on_delete=models.CASCADE)

    class Meta:
        """
        `queryset.first()` doesn't work well after it's been sliced, as django
        forces queryset ordering for models without default one.
        So we have to test unordered models too.
        """
        app_label = 'abnorm'
        ordering = None


class RelatedTestObj(BaseModel):
    value = models.IntegerField(default=0)
    test_obj = models.ForeignKey(
        TestObj, related_name='rto_items', on_delete=models.CASCADE)
    test_obj_wo_related_name = models.ForeignKey(
        TestObj, on_delete=models.CASCADE, null=True)

    class Meta:
        app_label = 'abnorm'
        ordering = ('id',)


class NullRelatedTestObj(BaseModel):
    value = models.IntegerField(default=0)
    test_obj = models.ForeignKey(
        TestObj, related_name='nrto_items', null=True, on_delete=models.CASCADE
    )

    class Meta:
        app_label = 'abnorm'
        ordering = ('id',)


class GenericRelatedTestObj(BaseModel):
    value = models.IntegerField(default=0)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    m2m_items = models.ManyToManyField('M2MTestObj')
    m2m_first_item = RelationField(
        'm2m_items', fields=('id', 'value'), limit=1, flat=True)

    class Meta:
        app_label = 'abnorm'
        ordering = ('id',)


class M2MTestObj(BaseModel):
    value = models.IntegerField(default=0)

    class Meta:
        app_label = 'abnorm'
        ordering = ('id',)
