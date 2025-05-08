from django.db import models

class User(models.Model):
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    telegram_id  = models.BigIntegerField(null=True, blank=True, editable=False)
    first_name   = models.CharField(max_length=100, blank=True)
    name         = models.CharField(max_length=100, blank=True)
    iin          = models.CharField(max_length=12, blank=True)      # ИИН обычно 12 символов
    t_number     = models.CharField(max_length=50, blank=True)      # табельный номер
    isadmin      = models.BooleanField(default=False)
    intent       = models.CharField(max_length=100, blank=True)
    linked_amount= models.IntegerField(default=0)
    phone        = models.CharField(max_length=20, blank=True)
    
    class Meta:
        db_table = '"portal"."users"'
        managed = True

    def __str__(self):
        return f"{self.name or ''} {self.first_name or ''} (ID={self.id})"


class Linked(models.Model):
    created_at  = models.DateTimeField(auto_now_add=True)
    telegram_id = models.BigIntegerField(null=True, blank=True)
    iin         = models.CharField(max_length=12, blank=True)
    t_number    = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = '"portal"."linked"'
        managed = True

    def __str__(self):
        return f"Linked {self.id} (tg_id={self.telegram_id}, t_number={self.t_number})"


class AuthUser(models.Model):
    user          = models.ForeignKey(
                        User,
                        on_delete=models.CASCADE,
                        db_column='user_id',
                        null=True,
                        blank=True
                    )
    password_hash = models.CharField(max_length=128)

    class Meta:
        db_table = '"portal"."auth_users"'
        managed = True

    def __str__(self):
        return f"AuthUser for User ID={self.user_id}"


class Department(models.Model):
    name       = models.CharField(
                    max_length=100,
                    unique=True,
                    help_text="Название отдела"
                 )
    description= models.TextField(
                    blank=True,
                    null=True,
                    help_text="Описание отдела (необязательно)"
                 )
    folder_id  = models.CharField(
                    max_length=255,
                    blank=True,
                    null=True,
                    help_text="ID папки Google Drive"
                 )

    class Meta:
        db_table = '"portal"."departments"'
        managed = True

    def __str__(self):
        return self.name


class UserDepartmentMapping(models.Model):
    """
    Связь один-к-одному между User и Department.
    """
    user       = models.OneToOneField(
                     User,
                     on_delete=models.CASCADE,
                     primary_key=True,
                     related_name='department_mapping'
                  )
    department = models.ForeignKey(
                     Department,
                     on_delete=models.SET_NULL,
                     null=True,
                     blank=True,
                     help_text="Отдел, в котором работает пользователь"
                 )

    class Meta:
        db_table = '"portal"."user_department_mappings"'
        managed = True

    def __str__(self):
        dep = self.department.name if self.department else "Не определён"
        return f"Пользователь {self.user} (Отдел: {dep})"
