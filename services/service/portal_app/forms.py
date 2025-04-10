from django import forms
from django.contrib.auth.hashers import make_password
from .models import AuthUser

class AuthUserForm(forms.ModelForm):
    """
    Форма для изменения пароля: админ вводит сырой пароль в поле password_raw.
    Поле password_hash заполняется автоматически при сохранении.
    """
    password_raw = forms.CharField(
        label="Пароль",
        required=True,
        widget=forms.PasswordInput,
        help_text="Введите сырой пароль, который будет захеширован."
    )

    class Meta:
        model = AuthUser
        # Используем только поля user и password_raw
        fields = ['user', 'password_raw']

    def save(self, commit=True):
        # Получаем экземпляр модели без сохранения в базу
        instance = super().save(commit=False)
        raw_pass = self.cleaned_data.get('password_raw')
        # Хэшируем введённый сырой пароль и сохраняем его в поле password_hash
        instance.password_hash = make_password(raw_pass)
        if commit:
            instance.save()
        return instance
