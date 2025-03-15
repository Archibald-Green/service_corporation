# portal_app/forms.py
from django import forms
from django.contrib.auth.hashers import make_password
from .models import AuthUser

class AuthUserForm(forms.ModelForm):
    """
    Форма, где админ вводит сырой пароль в поле password_raw.
    user - это ForeignKey на User (dropdown).
    """
    password_raw = forms.CharField(
        label="Пароль",
        required=False,
        widget=forms.PasswordInput,
        help_text="Введите сырой пароль, который будет захеширован."
    )

    class Meta:
        model = AuthUser
        # вместо 'user_id' используем 'user'
        fields = ['user', 'password_hash', 'password_raw']
        # можно убрать password_hash из fields, если хотим скрыть хэш

    def clean(self):
        cleaned_data = super().clean()
        raw_pass = cleaned_data.get('password_raw')
        print("DEBUG: raw_pass =", raw_pass)  # << отладка
        if raw_pass:
            hashed = make_password(raw_pass)
            print("DEBUG: hashed =", hashed)  # << отладка
            cleaned_data['password_hash'] = hashed
        return cleaned_data
