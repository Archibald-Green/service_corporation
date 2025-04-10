from django.contrib import admin

from .models import User, Linked, AuthUser, Department, UserDepartmentMapping
from .forms import AuthUserForm

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'first_name', 'iin', 'isadmin', 'created_at')
    search_fields = ('name', 'first_name', 'iin')
    list_filter = ('isadmin',)
    readonly_fields = ("telegram_id",)


@admin.register(Linked)
class LinkedAdmin(admin.ModelAdmin):
    list_display = ('id', 'telegram_id', 't_number', 'iin', 'created_at')
    search_fields = ('telegram_id', 't_number', 'iin')
    
@admin.register(AuthUser)
class AuthUserAdmin(admin.ModelAdmin):
    form = AuthUserForm
    list_display = ("id", "user", "password_hash")
    readonly_fields = ("password_hash",)

    def save_model(self, request, obj, form, change):
        """
        Вызывается при сохранении записи в админке.
        form.cleaned_data уже содержит новое password_hash (из clean()).
        """
        # Берём password_hash из cleaned_data
        new_hash = form.cleaned_data.get("password_hash")
        if new_hash:
            obj.password_hash = new_hash
        super().save_model(request, obj, form, change)
        
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'folder_id', 'description')
    search_fields = ('name', 'folder_id')

@admin.register(UserDepartmentMapping)
class UserDepartmentMappingAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
    search_fields = ('user__name', 'department__name')