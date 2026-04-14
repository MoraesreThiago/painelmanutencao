from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import FormView

from apps.accounts.forms import LoginForm
from apps.accounts.services import authenticate_user, login_redirect_for


class LoginView(FormView):
    template_name = "accounts/login.html"
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(login_redirect_for(request.user))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: LoginForm) -> HttpResponse:
        user = authenticate_user(
            request=self.request,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        if not user:
            form.add_error(None, "Credenciais inválidas.")
            return self.form_invalid(form)
        if not user.is_active:
            form.add_error(None, "Usuário inativo.")
            return self.form_invalid(form)

        login(self.request, user)
        self.request.session.set_expiry(None if form.cleaned_data["remember_me"] else 0)
        return redirect(login_redirect_for(user))


class LogoutView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "Sessão encerrada com sucesso.")
        return redirect("accounts:login")
