from __future__ import absolute_import


def setup_rules():
    try:
        from south.modelsinspector import add_introspection_rules
    except ImportError:
        return

    from ..fields import CountField, RelationField, SumField, AvgField
    rules = [
        (
            (CountField, RelationField),
            [],
            {
                "relation_name": ["relation_name", {}],
                "backwards_name": ["backwards_name", {}],
            },
        ),
        (
            (SumField, AvgField),
            [],
            {
                "relation_name": ["relation_name", {}],
                "field_name": ["field_name", {}],
                "backwards_name": ["backwards_name", {}],
            },
        ),
        (
            (RelationField,),
            [],
            {
                "fields": ["fields", {}],
                "flat": ["flat", {}],
                "limit": ["limit", {}],
            },
        ),
    ]
    add_introspection_rules(rules, ["^abnorm\."])
