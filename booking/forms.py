from django import forms
from .models import Appointment
from users.models import UserProfile
from catalog.models import Service
from crm.models import Customer
from django.db.models import Q

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['customer', 'service', 'provider', 'date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)
        if self.business:
            self.fields['customer'].queryset = Customer.objects.filter(business=self.business)
            self.fields['service'].queryset = Service.objects.filter(category__business=self.business)
            self.fields['provider'].queryset = UserProfile.objects.filter(business=self.business, role='provider')

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', 'End time must be later than start time.')

        if self.business and date and start_time and end_time:
            overlap_exists = Appointment.objects.filter(
                business=self.business,
                date=date,
            ).filter(
                Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
            ).exists()
            if overlap_exists:
                raise forms.ValidationError('This time slot overlaps with an existing appointment.')

        return cleaned_data
