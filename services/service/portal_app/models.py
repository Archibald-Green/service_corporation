from django.db import models

class User(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    telegram_id = models.BigIntegerField(null=True, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100, blank=True)
    iin = models.CharField(max_length=12, blank=True)      # ИИН обычно 12 символов
    t_number = models.CharField(max_length=50, blank=True) # табельный номер
    isadmin = models.BooleanField(default=False)
    intent = models.CharField(max_length=100, blank=True)
    linked_amount = models.IntegerField(default=0)
    phone = models.CharField(max_length=20, blank=True)
    
    class Meta:
        db_table = 'users'
        managed = False

    def __str__(self):
        return f"{self.name or ''} {self.first_name or ''} (ID={self.id})"


class Linked(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    telegram_id = models.BigIntegerField(null=True, blank=True)
    iin = models.CharField(max_length=12, blank=True)
    t_number = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'linked' 

    def __str__(self):
        return f"Linked {self.id} (tg_id={self.telegram_id}, t_number={self.t_number})"


class AuthUser(models.Model):
    user = models.ForeignKey(
        'portal_app.User',
        on_delete=models.CASCADE,
        db_column='user_id',
        null=True,              # разрешаем NULL
        blank=True
    )
    password_hash = models.CharField(max_length=128)
    

    class Meta:
        db_table = 'auth_users'
        managed = True


