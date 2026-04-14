from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.accounts.managers import UserManager
from common.models import UUIDTimeStampedModel
from common.permissions import get_user_permissions


class User(AbstractBaseUser, PermissionsMixin, UUIDTimeStampedModel):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    registration_number = models.CharField(max_length=80, unique=True, blank=True, null=True)
    job_title = models.CharField(max_length=120, blank=True, null=True)
    phone = models.CharField(max_length=40, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(blank=True, null=True)
    area = models.ForeignKey(
        "unidades.Area",
        related_name="primary_users",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    fabrica = models.ForeignKey(
        "unidades.Fabrica",
        related_name="scoped_users",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    unidade = models.ForeignKey(
        "unidades.UnidadeProdutiva",
        related_name="assigned_users",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    role = models.ForeignKey(
        "access.Role",
        related_name="users",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    allowed_areas = models.ManyToManyField(
        "unidades.Area",
        through="access.UserArea",
        related_name="authorized_users",
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        ordering = ["full_name", "email"]
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self) -> str:
        return self.full_name or self.email

    @property
    def area_ids(self) -> list[str]:
        area_ids = list(self.allowed_areas.values_list("id", flat=True))
        if self.area_id and self.area_id not in area_ids:
            area_ids.append(self.area_id)
        return [str(value) for value in area_ids]

    @property
    def permissions(self) -> set[str]:
        return {permission.value for permission in get_user_permissions(self)}
