# service/dbrouters.py

class AppRouter:
    """
    — Все модели из meter_app (и саму таблицу django_migrations) кладём в БД 'meter'.
    — Всё остальное (portal_app + встроенные Django-приложения) — в БД 'default'.
    """
    def db_for_read(self, model, **hints):
        return "meter" if model._meta.app_label == "meter_app" else "default"

    def db_for_write(self, model, **hints):
        return "meter" if model._meta.app_label == "meter_app" else "default"

    def allow_relation(self, obj1, obj2, **hints):
        db1 = "meter" if obj1._meta.app_label == "meter_app" else "default"
        db2 = "meter" if obj2._meta.app_label == "meter_app" else "default"
        return db1 == db2

    def allow_migrate(self, db, app_label, **hints):
        if db == "meter":
            # разрешаем миграции только для meter_app и для самой системы миграций
            return app_label == "meter_app" or app_label == "migrations"
        if db == "default":
            # в default блокируем meter_app, остальным (portal_app + auth, contenttypes, sessions и т.д.) — разрешаем
            return app_label != "meter_app"
        return None
