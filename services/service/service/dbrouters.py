class PortalRouter:
    """
    Модели из portal_app → база 'default' (portal_db).
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == "portal_app":
            return "default"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "portal_app":
            return "default"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == "portal_app" and obj2._meta.app_label == "portal_app":
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == "portal_app":
            return db == "default"
        return None


class MeterRouter:
    """
    Модели из meter_app → база 'meter' (meter_db).
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == "meter_app":
            return "meter"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "meter_app":
            return "meter"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == "meter_app" and obj2._meta.app_label == "meter_app":
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == "meter_app":
            return db == "meter"
        return None