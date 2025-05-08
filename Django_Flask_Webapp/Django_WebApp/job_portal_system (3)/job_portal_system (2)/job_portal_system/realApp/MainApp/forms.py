from django import forms
from .models import Job, JobApplication

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = '__all__'

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['job']
        widgets = {
            'job': forms.Select(),  # Or use forms.RadioSelect if you want to list them
        }
