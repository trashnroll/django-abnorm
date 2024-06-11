django-abnorm
=============

.. image:: https://github.com/trashnroll/django-abnorm/actions/workflows/test.yml/badge.svg?branch=master
    :target: https://github.com/trashnroll/django-abnorm/actions?workflow=test
    :alt: Build Status

Abnorm is a django denormalization toolkit.

It provides a set of extra model fields to ease the implementation of some typical denormalization scenarios by elimination of handwritten boilerplate code.

Abnorm relies on standard django signals machinery, so its basically (excluding some contrib fields) db agnostic - just as django ORM is.


TL;DR
-----

The following example gets your data denormalized with no boilerplate code.

.. code:: python

    # models.py

    import abnorm
    from django.db import models

    class Comment(models.Model):
        post = models.ForeignKey('Post', on_delete=models.CASCADE)
        text = models.TextField()


    class Post(models.Model):
        comment_count = abnorm.CountField('comment_set')
        first_comment = abnorm.RelationField(
            relation_name='comment_set', fields=('id', 'text'), limit=1,
            flat=True)

    # tests.py

    from django.test import TestCase

    from .models import Post, Comment


    class DummyTest(TestCase):

        def test_abnorm(self):
            post = Post.objects.create()

            # lets add a comment for the blog post
            Comment.objects.create(post=post)

            # abnorm magic happened, so we already have correct value for a
            # corresponding comment_count and first_comment fields in the db

            # now we just have to refresh post instance to get its fields
            # updated
            post.refresh_from_db()

            # TADA!
            self.assertEqual(post.comment_count, 1)
            self.assertEqual(post.first_comment, post.comment_set.first())


How it works
------------

Abnorm automatically creates and connects signal receivers with boring logic under the hood to handle almost every common case of related data modification as denormalized fields update trigger, except for ORM update statements, as they bypass signals entirely.

The only requirement for the augmented model (the one with abnorm field added to hold denormalized value) is to have a standard django relation descriptor, as it is internally used to reach the desired data source. You can use, for example, standard backwards relation accessors, that are auto-created for relationship fields.

Abnorm currently supports django 2.2-4.2 and recent versions of python3.

Work on documentation and tests is in progress, any help would be appreciated.

Fields
------

The following arguments are available to all field types:
    - `relation_name` - points to the denormalized data source accessor
    - `qs_filter` - takes a dict or Q with extra filtration parameters for the related data queryset

CountField
^^^^^^^^^^

Provides the actual related items count. A typical case would be, say, a number of comments for a blog post.

Has no extra params.

Example:

.. code:: python

    class Comment(models.Model):
        post = models.ForeignKey('Post', on_delete=models.CASCADE)

    class Post(models.Model):
        comment_count = abnorm.CountField('comment_set')

There's one more, with qs filtration - that one will count only comments with ``is_deleted == False``:

.. code:: python

    class Comment(models.Model):
        post = models.ForeignKey('Post', on_delete=models.CASCADE)
        is_deleted = models.BooleanField(default=False)

    class Post(models.Model):
        comment_count = abnorm.CountField(
            relation_name='comment_set', qs_filter={'is_deleted': False})

SumField
^^^^^^^^

Supplies the actual sum of specific foreign model field values.

Extra params:
    - `internal_type` - internal field type, used to store and validate your data, e.g. `IntegerField` or `DecimalField`
    - `field_name` - name of the foreign model field, that holds collected values

Example:

.. code:: python

    class Transaction(models.Model):
        account = models.ForeignKey(
            'Account', related_name='transactions', on_delete=models.CASCADE)
        amount = models.IntegerField(default=0)

    class Account(models.Model):
        balance = abnorm.SumField(
            relation_name='transactions', field_name='amount')


(obviously, this approach is not recommended for maintaining the actual account balance)


AvgField
^^^^^^^^

Maintains the actual average value of specific foreign model field values.

Extra params:

    - `internal_type`
    - `field_name`

Same as above, see `SumField` for details.


RelationField
^^^^^^^^^^^^^

Stores serialized set of related foreign model instances (fk, m2m, generic fk - whatever you may need) - entire records or specific fields only. Appears/behaves just like evaluated queryset to the end user, however, it saves you some precious db hits.

Extra params:

    - `fields` - required list of serialized field names
    - `limit` - number of records to store
    - `flat` - use to unwrap the result list with a single item in it, requires `limit=1`

Example:

.. code:: python

    class Comment(models.Model):
        post = models.ForeignKey('Post', on_delete=models.CASCADE)
        is_deleted = models.BooleanField(default=False)

    class Post(models.Model):
        first_five_comments = abnorm.RelationField(
            relation_name='comment_set',
            qs_filter={'is_deleted': False},
            limit=5)


Bang! This post's first_five_comments field now stores first 5 comments (as a list), and you can immediately use them with no extra db queries.


Miscellaneous
=============

contrib.RelationValueSetField
-----------------------------

Extracts and stores a set of foreign model single field values. Defaults to empty list.
This field is available only with postgres db backend, as it uses django.contrib.postgres.fields.ArrayField as a base class.

Extra params:

    - `default=list` - regular django field ``default`` parameter, so it can be callable
    - `field_name` - a name of a foreign model field to collect its values

Example:

.. code:: python

    class Comment(models.Model):
        post = models.ForeignKey('Post', on_delete=models.CASCADE)
        author_name = models.CharField(max_length=100)


    class Post(models.Model):
        comment_author_names = RelationValueSetField(
            relation_name='comment_set',
            default=list,
            field_name='author_name')


Custom fields
-------------

You can use DenormalizedFieldMixin to implement your own denormalized fields with custom data extraction logic. See the source code for examples.
