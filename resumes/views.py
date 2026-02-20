from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from .models import Job, Application, Profile
from .forms import CandidateSignUpForm, RecruiterSignUpForm, ApplicationForm, JobForm
from .ml_model import score_resume_for_job, get_matched_skills
from .utils import extract_text_from_file
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.utils import timezone
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password, get_default_password_validators
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST


def password_reset(request):
    if request.method == "POST":
        email = request.POST.get('email')
        new_password = request.POST.get('newpassword')
        confirm_password = request.POST.get('confirmpassword')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('password_reset')

        try:
            user = User.objects.get(email=email) 
            user.password = make_password(new_password)
            user.save()
            messages.success(request, "Password changed successfully.")
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "Invalid email or not an admin.")
    
    return render(request, "resumes/reset_password.html")


def signup_candidate(request):
    if request.method == 'POST':
        form = CandidateSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role='candidate')
            login(request, user)
            return redirect('resumes:job_list')
    else:
        form = CandidateSignUpForm()
    return render(request, 'resumes/signup_candidate.html', {'form': form})

def signup_recruiter(request):
    if request.method == 'POST':
        form = RecruiterSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # read cleaned company fields
            company = form.cleaned_data.get('company','')
            website = form.cleaned_data.get('company_website','')
            phone = form.cleaned_data.get('company_phone','')
            address = form.cleaned_data.get('company_address','')
            description = form.cleaned_data.get('company_description','')
            Profile.objects.create(
                user=user,
                role='recruiter',
                company=company,
                company_website=website,
                company_phone=phone,
                company_address=address,
                company_description=description
            )
            login(request, user)
            return redirect('resumes:recruiter_dashboard')
    else:
        form = RecruiterSignUpForm()
    return render(request, 'resumes/signup_recruiter.html', {'form': form})

class RecruiterProfileForm(forms.ModelForm):
    # allow editing username/email on the same form if you want:
    username = forms.CharField(required=True, label='Username')
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = Profile
        fields = [
            'company', 'company_website', 'company_phone',
            'company_address', 'company_description'
        ]
        widgets = {
            'company_address': forms.Textarea(attrs={'rows':2}),
            'company_description': forms.Textarea(attrs={'rows':3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        # pass user to initialize username/email from User model
        self.user = user
        super().__init__(*args, **kwargs)
        # Tailwind classes for visible inputs
        cls = 'w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-200'
        # for profile fields
        for fname in self.fields:
            self.fields[fname].widget.attrs.update({'class': cls, 'placeholder': self.fields[fname].label})
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


# --- View: recruiter_profile (read-only) ---
@login_required
def recruiter_profile(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter':
        return redirect('resumes:job_list')
    profile = request.user.profile
    return render(request, 'resumes/recruiter_profile.html', {'profile': profile})

# --- View: recruiter_profile_edit (edit form) ---
@login_required
def recruiter_profile_edit(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter':
        return redirect('resumes:job_list')
    profile = request.user.profile
    if request.method == 'POST':
        form = RecruiterProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('resumes:recruiter_profile')
    else:
        # initialize username/email from user
        initial = {'username': request.user.username, 'email': request.user.email}
        form = RecruiterProfileForm(instance=profile, initial=initial, user=request.user)
    return render(request, 'resumes/recruiter_profile_edit.html', {'form': form})

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep user logged in
            messages.success(request, 'Your password has been updated successfully!')
            form = PasswordChangeForm(request.user)  # reset form after success
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'resumes/change_password.html', {'form': form})

def job_list(request):
    qs = Job.objects.order_by('-created_at')
    q = request.GET.get('q','').strip()
    company = request.GET.get('company','').strip()
    location = request.GET.get('location','').strip()

    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(description__icontains=q)
    if company:
        qs = qs.filter(company__icontains=company)
    if location:
        qs = qs.filter(location__icontains=location)

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    jobs = paginator.get_page(page)

    # 🔹 Build applied_job_ids just like in candidate_dashboard
    applied_job_ids = set()
    if (
        request.user.is_authenticated
        and hasattr(request.user, 'profile')
        and request.user.profile.role == 'candidate'
    ):
        apps = Application.objects.filter(user=request.user).only('job_id')
        applied_job_ids = set(a.job_id for a in apps)

    return render(
        request,
        'resumes/job_list.html',
        {
            'jobs': jobs,
            'q': q,
            'company': company,
            'location': location,
            'applied_job_ids': applied_job_ids,   # ⭐ important
        }
    )

def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    applied = False
    if request.user.is_authenticated:
        applied = Application.objects.filter(user=request.user, job=job).exists()

    # compute expired based on application_deadline
    today = timezone.localdate()
    expired = False
    if job.application_deadline:
        expired = job.application_deadline < today

    return render(request, 'resumes/job_detail.html', {
        'job': job,
        'applied': applied,
        'expired': expired,
    })

@login_required
def apply_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    today = timezone.localdate()
    if job.application_deadline and job.application_deadline < today:
        messages.error(request, "The application deadline for this job has passed. You cannot apply.")
        return redirect('resumes:job_detail', pk=pk)
    # only candidates can apply
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'candidate':
        return redirect('resumes:job_detail', pk=pk)
    application, created = Application.objects.get_or_create(user=request.user, job=job)

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            app = form.save(commit=False)
            f = request.FILES.get('resume_file')
            if f:
                app.resume_file = f
                app.save()
                fpath = app.resume_file.path
                extracted = extract_text_from_file(fpath)
                if extracted:
                    app.resume_text = extracted
                    print("Extracted length:", len(app.resume_text or ""))
                    print("First 300 chars:", (app.resume_text or "")[:300])

            score = score_resume_for_job(app.resume_text or '', job)

            # Ensure score is percentage
            if score is not None:
                #score = float(score) * 100 if score <= 1 else float(score)
                score = float(score) * 100  # convert to percentage

            #app.score = score_resume_for_job(app.resume_text or '', job)
            app.score = round(score, 2)
            app.save()

            # notify recruiter via console email
            try:
                if job.posted_by and job.posted_by.email:
                    send_mail(f'New application for {job.title}', f'{request.user.username} applied.', 'no-reply@example.com', [job.posted_by.email], fail_silently=True)
            except Exception:
                pass
            return redirect('resumes:candidate_dashboard')
    else:
        form = ApplicationForm(instance=application)
    return render(request, 'resumes/apply_job.html', {'form': form, 'job': job})

@login_required
def candidate_dashboard(request):
    # only candidates
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'candidate':
        return redirect('resumes:job_list')
    apps = Application.objects.filter(user=request.user).select_related('job').order_by('-applied_at')
    jobs = Job.objects.order_by('-created_at')
    applied_job_ids = set(a.job_id for a in apps)
    today = timezone.localdate()
    job_expired = {}
    for j in jobs:
        job_expired[j.id] = bool(j.application_deadline and j.application_deadline < today)

    # Compute matched skills for each application (small, on-the-fly)
    application_skills = {}
    for a in apps:
        try:
            skills = get_matched_skills(a.resume_text or '', a.job)
        except Exception:
            skills = []
        application_skills[a.id] = skills

    return render(request, 'resumes/candidate_dashboard.html', {
        'applications': apps,
        'jobs': jobs,
        'applied_job_ids': applied_job_ids,
        'application_skills': application_skills,
         'job_expired': job_expired,
    })

@login_required
def recruiter_dashboard(request):
    # only recruiters
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter':
        return redirect('resumes:job_list')
    jobs = Job.objects.filter(posted_by=request.user).order_by('-created_at')
    return render(request, 'resumes/recruiter_dashboard.html', {'jobs': jobs})

@login_required
def job_create(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter':
        return redirect('resumes:job_list')
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            return redirect('resumes:recruiter_dashboard')
    else:
        form = JobForm()
    return render(request, 'resumes/job_create.html', {'form': form})



@login_required
def view_applicants(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter' or job.posted_by != request.user:
        return redirect('resumes:recruiter_dashboard')

    qs = Application.objects.filter(job=job).select_related('user').order_by('-applied_at')

    # paginate the queryset
    per_page = 5
    paginator = Paginator(qs, per_page)
    page = request.GET.get('page')

    try:
        apps_page = paginator.page(page)
    except PageNotAnInteger:
        apps_page = paginator.page(1)
    except EmptyPage:
        apps_page = paginator.page(paginator.num_pages)

    # compute metadata for only the current page's objects
    apps_with_meta = []
    for a in apps_page.object_list:
        resume_text = a.resume_text or ''
        score = a.score
        skills = get_matched_skills(resume_text, job)
        apps_with_meta.append({
            'application': a,
            'score': score,
            'skills': skills,
        })

    return render(request, 'resumes/view_applicants.html', {
        'apps_with_meta': apps_with_meta,
        'job': job,
        'page_obj': apps_page,
        'paginator': paginator,
        'is_paginated': apps_page.has_other_pages(),
    })

@login_required
def admin_dashboard(request):
    # only admins (profile role admin) - custom dashboard
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
        return redirect('resumes:job_list')
    total_users = User.objects.count()
    total_jobs = Job.objects.count()
    total_apps = Application.objects.count()
    return render(request, 'resumes/admin_dashboard.html', {'total_users': total_users, 'total_jobs': total_jobs, 'total_apps': total_apps})

@login_required
def ml_score_view(request, application_id):
    app = get_object_or_404(Application, pk=application_id, user=request.user)
    # compute matched skills for display
    try:
        matched_skills = get_matched_skills(app.resume_text or '', app.job)
    except Exception:
        matched_skills = []
    return render(request, 'resumes/ml_score.html', {'application': app, 'matched_skills': matched_skills})

def role_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')

    role = request.user.profile.role

    if role == 'candidate':
        return redirect('resumes:candidate_dashboard')

    elif role == 'recruiter':
        return redirect('resumes:recruiter_dashboard')

    elif role == 'admin':
        return redirect('resumes:admin_dashboard')

    return redirect('/')


@login_required
def application_history(request):
    if not hasattr(request.user, "profile") or request.user.profile.role != "candidate":
        return redirect("resumes:job_list")

    apps = (
        Application.objects.filter(user=request.user)
        .select_related("job")
        .order_by("-applied_at")
    )

    return render(request, "resumes/application_history.html", {
        "applications": apps
    })


@login_required
@require_POST
def set_application_status(request, app_id):
    
    try:
        app = Application.objects.select_related('job', 'job__posted_by').get(pk=app_id)
    except Application.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    # permission: only recruiter who posted the job (or admin) can change
    user_profile = getattr(request.user, 'profile', None)
    is_admin = user_profile and user_profile.role == 'admin'
    if not (is_admin or (user_profile and user_profile.role == 'recruiter' and app.job.posted_by == request.user)):
        return HttpResponseForbidden("You don't have permission to change this application status.")

    status = request.POST.get('status')
    if status not in dict(Application.STATUS_CHOICES):
        return JsonResponse({'error': 'Invalid status'}, status=400)

    app.status = status
    app.save(update_fields=['status'])

    # optionally: notify candidate via email (console in development)
    try:
        if app.user.email:
            send_mail(
                f'Application status updated for {app.job.title}',
                f'Your application status is now: {app.get_status_display()}',
                'no-reply@example.com',
                [app.user.email],
                fail_silently=True,
            )
    except Exception:
        pass

    # Return JSON for AJAX, or redirect if requested
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'status': status})
    return redirect('resumes:view_applicants', pk=app.job.pk)