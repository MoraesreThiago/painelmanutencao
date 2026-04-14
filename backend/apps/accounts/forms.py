from __future__ import annotations

from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"placeholder": "admin@maintenance.example.com"}),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "Sua senha"}),
    )
    remember_me = forms.BooleanField(label="Lembrar de mim", required=False)
