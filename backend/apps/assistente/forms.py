from __future__ import annotations

from django import forms


class ChatPromptForm(forms.Form):
    session_id = forms.UUIDField(required=False, widget=forms.HiddenInput())
    prompt = forms.CharField(
        label="Mensagem",
        max_length=4000,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Pergunte algo sobre a operacao da sua area.",
            }
        ),
    )

    def clean_prompt(self):
        prompt = self.cleaned_data["prompt"].strip()
        if not prompt:
            raise forms.ValidationError("Digite uma pergunta para o assistente.")
        return prompt

