import json

from django import forms

from .models import ScrapeJob
from .services.scraping.validators import validate_url


class ScrapeJobForm(forms.ModelForm):
    custom_fields_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": '{"price": ".price", "author": ".author"}'}),
        help_text="Optional JSON object mapping field names to CSS selectors.",
    )

    class Meta:
        model = ScrapeJob
        fields = ["name", "url", "strategy", "schedule_enabled", "schedule_frequency", "max_pages", "max_records", "request_timeout", "request_delay"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Product scraper"}),
            "url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://example.com"}),
            "strategy": forms.Select(attrs={"class": "form-select"}),
            "schedule_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "schedule_frequency": forms.Select(attrs={"class": "form-select"}),
            "max_pages": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 20}),
            "max_records": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 5000}),
            "request_timeout": forms.NumberInput(attrs={"class": "form-control", "min": 5, "max": 120}),
            "request_delay": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 10, "step": "0.1"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["custom_fields_text"].initial = json.dumps(self.instance.custom_fields, indent=2) if self.instance.pk and self.instance.custom_fields else ""

    def clean_url(self):
        return validate_url(self.cleaned_data["url"])

    def clean_custom_fields_text(self):
        raw = self.cleaned_data["custom_fields_text"].strip()
        if not raw:
            return {}
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError("Custom fields must be valid JSON.") from exc
        if not isinstance(value, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in value.items()):
            raise forms.ValidationError("Custom fields must be a JSON object of field names and CSS selectors.")
        return value

    def save(self, commit=True):
        job = super().save(commit=False)
        job.custom_fields = self.cleaned_data.get("custom_fields_text", {})
        if commit:
            job.save()
        return job
