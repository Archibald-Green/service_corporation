from django.contrib import admin

from .models import User, Linked 

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'first_name', 'iin', 'isadmin', 'created_at')
    search_fields = ('name', 'first_name', 'iin')
    list_filter = ('isadmin',)

@admin.register(Linked)
class LinkedAdmin(admin.ModelAdmin):
    list_display = ('id', 'telegram_id', 't_number', 'iin', 'created_at')
    search_fields = ('telegram_id', 't_number', 'iin')