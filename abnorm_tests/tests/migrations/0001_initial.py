import abnorm.fields
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='M2MTestObj',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='TestParentObj',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('all_test_objs', abnorm.fields.RelationField(blank=True, default=[], fields=('id', 'm2m_first_2_items'), null=True, relation_name='test_objs')),
                ('all_children', abnorm.fields.RelationField(blank=True, default=[], fields=('id', 'all_test_objs'), null=True, relation_name='children')),
                ('first_test_obj', abnorm.fields.RelationField(blank=True, default=None, fields=('id', 'm2m_first_2_items', 'm2m_first_item'), flat=True, limit=1, null=True, relation_name='test_objs')),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='tests.TestParentObj')),
            ],
        ),
        migrations.CreateModel(
            name='TestObj',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rto_item_values_sum', abnorm.fields.SumField(blank=True, default=0, field_name='value', internal_type=django.db.models.fields.IntegerField, null=True, relation_name='rto_items')),
                ('rto_with_default_related_name_item_values_sum', abnorm.fields.SumField(blank=True, default=0, field_name='value', internal_type=django.db.models.fields.IntegerField, null=True, relation_name='relatedtestobj_set')),
                ('rto_items_count', abnorm.fields.CountField(blank=True, default=0, null=True, relation_name='rto_items')),
                ('rto_items_qsf_count', abnorm.fields.CountField(blank=True, default=0, null=True, relation_name='rto_items')),
                ('rto_items_qsfq_count', abnorm.fields.CountField(blank=True, default=0, null=True, relation_name='rto_items')),
                ('rto_first_item', abnorm.fields.RelationField(blank=True, default=None, fields=('id', 'value', 'test_obj_id'), flat=True, limit=1, null=True, relation_name='rto_items')),
                ('rto_first_2_items', abnorm.fields.RelationField(blank=True, default=[], fields=('id', 'value'), limit=2, null=True, relation_name='rto_items')),
                ('nrto_item_values_sum', abnorm.fields.SumField(blank=True, default=0, field_name='value', internal_type=django.db.models.fields.IntegerField, null=True, relation_name='nrto_items')),
                ('nrto_items_count', abnorm.fields.CountField(blank=True, default=0, null=True, relation_name='nrto_items')),
                ('nrto_first_item', abnorm.fields.RelationField(blank=True, default=None, fields=('id', 'value'), flat=True, limit=1, null=True, relation_name='nrto_items')),
                ('nrto_first_2_items', abnorm.fields.RelationField(blank=True, default=[], fields=('id', 'value'), limit=2, null=True, relation_name='nrto_items')),
                ('grto_item_values_sum', abnorm.fields.SumField(blank=True, default=0, field_name='value', internal_type=django.db.models.fields.IntegerField, null=True, relation_name='grto_items')),
                ('grto_items_count', abnorm.fields.CountField(blank=True, default=0, null=True, relation_name='grto_items')),
                ('grto_first_item', abnorm.fields.RelationField(blank=True, default=None, fields=('id', 'value', 'm2m_first_item'), flat=True, limit=1, null=True, relation_name='grto_items')),
                ('grto_first_2_items', abnorm.fields.RelationField(blank=True, default=[], fields=('id', 'value'), limit=2, null=True, relation_name='grto_items')),
                ('m2m_item_values_sum', abnorm.fields.SumField(blank=True, default=0, field_name='value', internal_type=django.db.models.fields.IntegerField, null=True, relation_name='m2m_items')),
                ('m2m_items_count', abnorm.fields.CountField(blank=True, default=0, null=True, relation_name='m2m_items')),
                ('m2m_first_item', abnorm.fields.RelationField(blank=True, default=None, fields=('id', 'value'), flat=True, limit=1, null=True, relation_name='m2m_items')),
                ('m2m_first_2_items', abnorm.fields.RelationField(blank=True, default=[], fields=('id', 'value'), limit=2, null=True, relation_name='m2m_items')),
                ('first_non_ordered', abnorm.fields.RelationField(blank=True, default=None, fields=('id', 'value'), flat=True, limit=1, null=True, relation_name='non_ordereds')),
                ('m2m_items', models.ManyToManyField(to='tests.M2MTestObj')),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='test_objs', to='tests.TestParentObj')),
            ],
        ),
        migrations.CreateModel(
            name='RelatedTestObj',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField(default=0)),
                ('test_obj', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rto_items', to='tests.TestObj')),
                ('test_obj_wo_related_name', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tests.TestObj')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='NullRelatedTestObj',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField(default=0)),
                ('test_obj', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='nrto_items', to='tests.TestObj')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='NonOrderedModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField(default=0)),
                ('test_obj', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='non_ordereds', to='tests.TestObj')),
            ],
            options={
                'ordering': None,
            },
        ),
        migrations.CreateModel(
            name='GenericRelatedTestObj',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField(default=0)),
                ('object_id', models.PositiveIntegerField()),
                ('m2m_first_item', abnorm.fields.RelationField(blank=True, default=None, fields=('id', 'value'), flat=True, limit=1, null=True, relation_name='m2m_items')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('m2m_items', models.ManyToManyField(to='tests.M2MTestObj')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
    ]
