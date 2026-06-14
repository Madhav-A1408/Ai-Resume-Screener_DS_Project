from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from ckeditor.widgets import CKEditorWidget
from .models import Job, Application, Profile
from django.core.exceptions import ValidationError


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class CandidateSignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        error_messages={
            'invalid': 'Enter a valid email address. Eg: abc@gmail.com'
        }
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    # ✅ Override BOTH username & email validation into ONE message
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')

        # # Check username
        # if username and User.objects.filter(username__iexact=username).exists():
        #     raise ValidationError("Account already registered, please log in.")

        # # Check email
        # if email and User.objects.filter(email__iexact=email).exists():
        #     raise ValidationError("Account already registered, please log in.")

        return cleaned_data

    # ✅ Styling + remove help text
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cls = 'w-full h-12 px-3 border border-gray-300 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition'

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': cls,
                'placeholder': self.fields[field].label
            })

            # ❌ Remove default help text
            self.fields[field].help_text = ""

        # ❌ Remove Django default username error
        self.fields['username'].error_messages['unique'] = "Account already registered, please log in."
        
            
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
        file = cleaned_data.get("resume_file")

        if not file:
            raise forms.ValidationError("Please upload a resume file.")

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
            
class CandidateProfileForm(forms.ModelForm):
    name = forms.CharField(required=True, label="Full Name")

    class Meta:
        model = Profile

        fields = [
            'profile_image',
            'phone',
            'location',
            'education',
            'skills',
            'experience',
            'projects',
            'languages',
            'profile_summary',
            'resume'
        ]

        widgets = {
            'profile_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'resume': forms.ClearableFileInput(attrs={'accept': '.pdf,.doc,.docx'}),

            'education': forms.Textarea(attrs={'rows':3}),
            'experience': forms.Textarea(attrs={'rows':3}),
            'projects': forms.Textarea(attrs={'rows':3}),
            'profile_summary': forms.Textarea(attrs={'rows':4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if user:
            self.fields['name'].initial = user.username

        # ⭐ Move name to the top
        self.order_fields([
            'name',
            'profile_image',
            'phone',
            'location',
            'education',
            'skills',
            'experience',
            'projects',
            'languages',
            'profile_summary',
            'resume'
        ])

        cls = "w-full p-2 border border-gray-300 rounded"
        for f in self.fields:
            self.fields[f].widget.attrs.update({'class': cls})
    def save(self, commit=True):
        profile = super().save(commit=False)

        if self.user:
            self.user.username = self.cleaned_data['name']
            if commit:
                self.user.save()

        if commit:
            profile.save()

        return profile
    
class RecruiterProfileForm(forms.ModelForm):
    
    username = forms.CharField(required=True, label='Username')
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = Profile
        fields = [
            'profile_image','company', 'company_website', 'company_phone',
            'company_address', 'company_description'
        ]
        widgets = {
            'profile_image': forms.FileInput(attrs={'accept': 'image/*','class': 'hidden','id': 'profile_image_input'}),
            'company_address': forms.Textarea(attrs={'rows':2}),
            'company_description': forms.Textarea(attrs={'rows':3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        # pass user to initialize username/email from User model
        self.user = user
        super().__init__(*args, **kwargs)
        # Tailwind classes for visible inputs
        cls = 'w-full p-2.5 border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-300 focus:border-green-500 transition duration-200'
        # for profile fields
        for fname in self.fields:
            if fname != 'profile_image':   # ✅ SKIP IMAGE FIELD
                self.fields[fname].widget.attrs.update({
                    'class': cls,
                    'placeholder': self.fields[fname].label
            })
        # add username/email fields separately (not in Meta)
        self.fields['username'].widget.attrs.update({'class': cls, 'placeholder': 'Username'})
        self.fields['email'].widget.attrs.update({'class': cls, 'placeholder': 'Email'})

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username=username).exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError('Username already taken')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email=email).exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError('Email already used')
        return email

    def save(self, commit=True):
        # save profile fields and update User username/email
        profile = super().save(commit=False)
        user = self.user
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.user = user
            profile.save()
        return profile