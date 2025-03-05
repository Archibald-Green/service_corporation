# service/dbrouters.py

class PortalRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'portal_app':
            return 'default'  # alias
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'portal_app':
            return 'default'
        return None


class MeterRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'meter_app':
            return 'meter'  # alias
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'meter_app':
            return 'meter'
        return None
