import gc

from funcy import distinct, group_values

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.decorators import method_decorator

from abnorm.adapters import this_django

try:
    from progress.bar import Bar
except ImportError:
    Bar = None


def queryset_iterator(queryset, chunksize=1000):
    last_item = queryset.order_by('-pk').first()
    if not last_item:
        return

    pk = 0
    queryset = queryset.order_by('pk')
    while pk < last_item.pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()


def with_progress_bar(queryset, message='', total=None):
    progress_bar = Bar(message, max=total or queryset.count())
    for instance in progress_bar.iter(queryset):
        yield instance
    progress_bar.finish()


class Command(BaseCommand):
    help = '''
    Updates specified abnorm fields (use `app_label.Model.field_name` notation)
    '''

    def add_arguments(self, parser):
        parser.add_argument('field', nargs='+')

    @method_decorator(transaction.atomic)
    def handle(self, *args, **options):
        # django 1.6/1.7 takes cmd args as `args`, 1.8+ as `options`
        # sum their values to support both ways
        fields = distinct(list(args) + options.get('field', []))
        groups = group_values(f.rsplit('.', 1) for f in fields)
        for model_name, field_names in groups.items():
            self.migrate_fields(model_name, field_names)

    def migrate_fields(self, model_name, field_names):
        model = this_django.get_model(model_name)
        queryset = model._base_manager.all()
        instances = queryset_iterator(queryset)

        if Bar is not None:
            instances = with_progress_bar(
                instances, message=model_name, total=queryset.count())

        for instance in instances:
            instance.save(update_fields=field_names)
