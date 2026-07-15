from django import forms

from leads.models import EnquiryMessage


class EnquiryCreateForm(forms.Form):
    subject = forms.CharField(max_length=255, required=False)
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=True)

    def clean_body(self):
        body = (self.cleaned_data.get("body") or "").strip()
        if not body:
            raise forms.ValidationError("Please write a short message.")
        return body


class EnquiryReplyForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=True)

    def clean_body(self):
        body = (self.cleaned_data.get("body") or "").strip()
        if not body:
            raise forms.ValidationError("Message cannot be empty.")
        return body
