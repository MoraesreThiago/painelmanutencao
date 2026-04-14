from __future__ import annotations

from django import forms

from common.enums import ExternalServiceStatus


class ServiceOrderFilterForm(forms.Form):
    search = forms.CharField(required=False, label="Busca")
    area = forms.ChoiceField(required=False, label="Area")
    status = forms.ChoiceField(
        required=False,
        label="Status",
        choices=[("", "Todos os status"), *ExternalServiceStatus.choices],
    )

    def __init__(self, *args, allowed_areas=None, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_areas = allowed_areas or []
        self.fields["search"].widget.attrs.update(
            {
                "placeholder": "OS, fornecedor, motor ou equipamento",
            }
        )
        self.fields["area"].choices = [("", "Todas as areas acessiveis")] + [
            (str(area.code), area.name) for area in allowed_areas
        ]
