from .adapters import this_django

delayed_setup_signals = []
signals_connected = []

SKIP_SIGNALS = this_django.is_migration_command_running()


class AbnormBlocker(object):
    def __init__(self):
        self.SKIP_SIGNALS = SKIP_SIGNALS

    def __enter__(self, *args, **kwargs):
        global SKIP_SIGNALS
        SKIP_SIGNALS = True

    def __exit__(self, *args, **kwargs):
        global SKIP_SIGNALS
        SKIP_SIGNALS = self.SKIP_SIGNALS
