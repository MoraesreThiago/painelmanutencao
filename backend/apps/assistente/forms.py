from __future__ import annotations

from django import forms

from apps.unidades.models import Area


class ChatPromptForm(forms.Form):
    session_id = forms.UUIDField(required=False, widget=forms.HiddenInput())
    area = forms.ChoiceField(required=False, label="Area")
    prompt = forms.CharField(
        label="Pergunta",
        max_length=4000,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Ex.: Me fale os principais motivos das ocorrencias dos ultimos 3 meses.",
            }
        ),
    )

    def __init__(self, *args, allowed_areas=None, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_areas = allowed_areas or []
        self.fields["area"].choices = [("", "Todas as areas acessiveis")] + [
            (str(area.code), area.name) for area in allowed_areas
        ]

    def clean_prompt(self):
        prompt = self.cleaned_data["prompt"].strip()
        if not prompt:
            raise forms.ValidationError("Digite uma pergunta para o assistente.")
        return prompt

