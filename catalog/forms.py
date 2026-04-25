from django import forms
from .models import Service, ServiceCategory

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['category', 'name', 'description', 'image_url', 'image', 'duration_mins', 'price', 'is_active']
        
    def __init__(self, *args, **kwargs):
        business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)
        if business:
            self.fields['category'].queryset = ServiceCategory.objects.filter(business=business)

    def clean_duration_mins(self):
        duration = self.cleaned_data['duration_mins']
        if duration <= 0:
            raise forms.ValidationError('Duration must be greater than 0 minutes.')
        return duration

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError('Price cannot be negative.')
        return price

    def clean_image_url(self):
        image_url = self.cleaned_data.get('image_url', '').strip()
        return image_url

class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name']

