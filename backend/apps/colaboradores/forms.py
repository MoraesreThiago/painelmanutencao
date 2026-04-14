from __future__ import annotations

from django import forms

from apps.unidades.services import get_fabricas_visiveis, get_unidades_visiveis
from common.enums import RecordStatus


class TeamFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        label="Busca textual",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Nome, matricula, cargo ou usuario",
            }
        ),
    )
    job_title = forms.CharField(
        required=False,
        label="Cargo",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Filtrar por cargo",
            }
        ),
    )
    status = forms.ChoiceField(
        required=False,
        label="Status",
        choices=[("", "Todos os status"), *RecordStatus.choices],
        widget=forms.Select(),
    )
    fabrica = forms.ChoiceField(
        required=False,
        label="Fabrica",
        choices=[("", "Todas as fabricas")],
        widget=forms.Select(),
    )
    unidade = forms.ChoiceField(
        required=False,
        label="Unidade",
        choices=[("", "Todas as unidades")],
        widget=forms.Select(),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        self.fields["fabrica"].choices = [
            ("", "Todas as fabricas"),
            *((fabrica.code, fabrica.name) for fabrica in get_fabricas_visiveis(user)),
        ]
        self.fields["unidade"].choices = [
            ("", "Todas as unidades"),
            *((str(unidade.id), f"{unidade.fabrica.name} - {unidade.name}") for unidade in get_unidades_visiveis(user)),
        ]
