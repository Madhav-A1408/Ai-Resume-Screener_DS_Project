from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from ckeditor.widgets import CKEditorWidget
from .models import Job, Application, Profile


class CandidateSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ('username','email','password1','password2')

class RecruiterSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    company = forms.CharField(required=False, label='Company name')
    company_website = forms.URLField(required=False, label='Website')
    company_phone = forms.CharField(required=False, label='Phone')
    company_address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':2}), label='Address')
    company_description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':3}), label='Company description')

    class Meta:
        model = User
        fields = ('username','email','password1','password2','company','company_website','company_phone','company_address','company_description')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # add Tailwind-friendly classes to widgets
        cls = 'w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-200'
        for fname in ('username','email','password1','password2','company','company_website','company_phone','company_address','company_description'):
            if fname in self.fields:
                self.fields[fname].widget.attrs.update({'class': cls, 'placeholder': self.fields[fname].label})

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('resume_text', 'resume_file')
        widgets = {
            'resume_text': forms.Textarea(attrs={
                'rows': 6,
                'class': 'w-full p-3 border rounded-lg'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get("resume_text")
        file = cleaned_data.get("resume_file")

        # Ensure at least one is provided
        if not text and not file:
            raise forms.ValidationError(
                "Please enter resume text or upload a resume file."
            )

        return cleaned_data

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company', 'location', 'description', 'skills','application_deadline']
        widgets = {
            'description': CKEditorWidget(config_name='default'),
            'skills': forms.TextInput(attrs={'placeholder': 'e.g. Python, Django, REST, SQL'}),
            'application_deadline': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls = 'w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-200'
        for fname in self.fields:
            self.fields[fname].widget.attrs.update({'class': cls})
