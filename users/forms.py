from django import forms
from .models import User, Business

class RegistrationForm(forms.Form):
    business_name = forms.CharField(max_length=255, required=True, label="Business Name")
    industry_type = forms.ChoiceField(choices=Business.INDUSTRY_CHOICES, required=True, label="Industry Type")
    email = forms.EmailField(required=True, label="Email Address")
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Password")
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class BusinessLandingForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = [
            'hero_title',
            'hero_subtitle',
            'hero_image_url',
            'public_phone',
            'public_email',
            'public_address',
            'map_embed_url',
            'testimonial_quote',
            'testimonial_author',
        ]
