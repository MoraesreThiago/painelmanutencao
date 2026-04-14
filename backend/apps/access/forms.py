from __future__ import annotations

from django import forms

from common.enums import RoleName
from common.permissions import ASSUMABLE_ROLE_NAMES, get_allowed_areas, has_actual_permission, PermissionName


class ContextSwitchForm(forms.Form):
    area = forms.ChoiceField(label="Área")
    role_name = forms.ChoiceField(label="Nível")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        if not has_actual_permission(user, PermissionName.ASSUME_AREA_CONTEXT):
            self.fields["area"].choices = []
            self.fields["role_name"].choices = []
            return

        allowed_areas = sorted(get_allowed_areas(user), key=lambda item: item.name)
        self.fields["area"].choices = [(area.code, area.name) for area in allowed_areas]
        self.fields["role_name"].choices = [
            (role_name.value, role_name.label)
            for role_name in ASSUMABLE_ROLE_NAMES
        ]
