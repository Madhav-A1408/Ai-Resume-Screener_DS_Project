from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from .models import Job, Application, Profile
from .forms import CandidateSignUpForm, RecruiterSignUpForm, ApplicationForm, JobForm, CandidateProfileForm,RecruiterProfileForm
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
import csv
from django.http import HttpResponse
from .models import Application
from datetime import timedelta
from django.db.models import Q
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods




import random
from .models import PasswordResetOTP

import random
from datetime import timedelta
from django.utils import timezone

def password_reset(request):
    if request.method == "POST":
        step = request.POST.get("step")

        # STEP 1 → SEND OTP
        if step == "send_otp":
            email = request.POST.get("email")

            try:
                user = User.objects.get(email=email)

                # 🔥 delete old OTPs
                PasswordResetOTP.objects.filter(user=user).delete()

                otp = str(random.randint(100000, 999999))

                otp_obj = PasswordResetOTP.objects.create(user=user, otp=otp)

                send_mail(
                    "Your Password Reset Code",
                    f"Your OTP is {otp}. It is valid for 1 minute.",
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )

                request.session['reset_email'] = email
                request.session['otp_time'] = otp_obj.created_at.timestamp()

                messages.success(request, "OTP sent to your email.")

                return render(request, "resumes/reset_password.html", {
                    "show_otp": True,
                    "otp_time": request.session.get('otp_time')
                })

            except User.DoesNotExist:
                messages.error(request, "Email not registered.")
                return render(request, "resumes/reset_password.html", {"show_otp": False})

        # STEP 2 → VERIFY OTP
        elif step == "verify_otp":
            otp = request.POST.get("otp")
            new_password = request.POST.get("newpassword")
            confirm_password = request.POST.get("confirmpassword")

            email = request.session.get('reset_email')

            if not email:
                messages.error(request, "Session expired.")
                return redirect('password_reset')

            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, "resumes/reset_password.html", {"show_otp": True})

            user = User.objects.get(email=email)

            otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp).last()

            if not otp_obj:
                messages.error(request, "Invalid OTP.")
                return render(request, "resumes/reset_password.html", {"show_otp": True})

            # ⏱ expiry check (1 minute)
            if timezone.now() > otp_obj.created_at + timedelta(minutes=1):
                messages.error(request, "OTP expired.")
                return redirect('password_reset')

            # ✅ RESET PASSWORD
            user.password = make_password(new_password)
            user.save()

            otp_obj.delete()

            messages.success(request, "Password reset successful.")
            return redirect('login')

    # ✅ DEFAULT (VERY IMPORTANT FIX)
    return render(request, "resumes/reset_password.html", {
        "show_otp": False
    })
def signup_candidate(request):
    if request.method == 'POST':
        form = CandidateSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role='candidate')

            login(request, user)

            # ✅ message ONLY when successful
            messages.success(request, "Welcome! Your account has been created.")

            return redirect('resumes:candidate_dashboard')

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
        form = RecruiterProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
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
    # qs = Job.objects.order_by('-created_at')
    today = timezone.localdate()

    # allow jobs to remain visible 2 days after deadline
    valid_date = today - timedelta(days=2)

    qs = Job.objects.filter(
        Q(application_deadline__isnull=True) |
        Q(application_deadline__gte=valid_date)
    ).order_by('-created_at')
    
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

    today = timezone.localdate()
    expired = False
    if job.application_deadline:
        expired = job.application_deadline < today

    # ✅ FIX: split skills here
    skills_list = []
    if job.skills:
        skills_list = [s.strip() for s in job.skills.split(',') if s.strip()]

    return render(request, 'resumes/job_detail.html', {
        'job': job,
        'applied': applied,
        'expired': expired,
        'skills_list': skills_list   # 👈 pass to template
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
                    app.save()   
                    print("Extracted length:", len(app.resume_text or ""))
                    print("First 300 chars:", (app.resume_text or "")[:300])

            score = score_resume_for_job(app.resume_text or '', job)

            if score is not None:
                score = float(score)
                MAX_EXPECTED = 0.45
                normalized_score = (score / MAX_EXPECTED) * 100
                normalized_score = min(normalized_score, 100)
                app.score = round(normalized_score, 2)
            else:
                app.score = 0

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

    # ✅ matched skills
    application_skills = {}
    for a in apps:
        try:
            skills = get_matched_skills(a.resume_text or '', a.job)
        except Exception:
            skills = []
        application_skills[a.id] = skills

    # ✅🔥 NEW: split profile skills for UI tags
    skills_list = []
    if request.user.profile.skills:
        skills_list = [
            s.strip() for s in request.user.profile.skills.split(',')
            if s.strip()
        ]
        
                # ✅ FORMAT EDUCATION FOR DISPLAY
    education_list = []

    if request.user.profile.education:
            entries = request.user.profile.education.split(",")

            for e in entries:
                parts = [p.strip() for p in e.split("|")]

                if len(parts) == 5:
                    education_list.append({
                        "degree": parts[0],
                        "spec": parts[1],
                        "college": parts[2],
                        "year": parts[3],
                        "cgpa": parts[4],
                    })

    return render(request, 'resumes/candidate_dashboard.html', {
        'applications': apps,
        'jobs': jobs,
        'applied_job_ids': applied_job_ids,
        'application_skills': application_skills,
        'job_expired': job_expired,

        # ✅ ADD THIS
        'skills_list': skills_list,
        'education_list': education_list,   # ✅ ADD THIS
    })

@login_required
def recruiter_dashboard(request):
    # only recruiters
    # if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter':
    #     return redirect('resumes:job_list')
    # jobs = Job.objects.filter(posted_by=request.user).order_by('-created_at')
    # return render(request, 'resumes/recruiter_dashboard.html', {'jobs': jobs})
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'recruiter':
        return redirect('resumes:job_list')

    today = timezone.localdate()

    jobs = Job.objects.filter(posted_by=request.user).order_by('-created_at')

    return render(request, 'resumes/recruiter_dashboard.html', {
        'jobs': jobs,
        'today': today
    })

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
def edit_job(request, job_id):
    job = get_object_or_404(Job,id=job_id)
    
    # ensure only recruiter who posted the job can edit
    if job.posted_by != request.user:
        return HttpResponseForbidden("You are not allowed to edit this job.")

    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully.")
            return redirect('resumes:recruiter_dashboard')
    else:
        form = JobForm(instance=job)  # prefill form with existing job data

    return render(request, "resumes/job_create.html", {"form": form , "edit_mode":True})
    

@login_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # ensure only recruiter who posted the job can delete
    if job.posted_by != request.user:
        return HttpResponseForbidden("You are not allowed to delete this job.")

    job.delete()
    messages.success(request, "Job deleted successfully.")

    return redirect('resumes:recruiter_dashboard')



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
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
        return redirect('resumes:job_list')

    if request.method == 'POST' and request.POST.get('action') == 'update_email':
        user_id = request.POST.get('user_id')
        new_email = request.POST.get('new_email', '').strip()

        target_user = get_object_or_404(User, pk=user_id)

        if User.objects.filter(email__iexact=new_email).exclude(pk=user_id).exists():
            messages.error(request, f"Email '{new_email}' is already used by another account.")
        elif new_email:
            target_user.email = new_email
            target_user.save()
            messages.success(request, f"Updated email for {target_user.username}.")

        return redirect('resumes:admin_dashboard')

    total_users = User.objects.count()
    total_jobs = Job.objects.count()
    total_apps = Application.objects.count()
    all_users = User.objects.select_related('profile').order_by('username')

    return render(request, 'resumes/admin_dashboard.html', {
        'total_users': total_users,
        'total_jobs': total_jobs,
        'total_apps': total_apps,
        'all_users': all_users,
    })
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

    if not hasattr(request.user, 'profile'):
        messages.error(request, "No account profile found. Please sign up first.")
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
        .select_related("job", "job__posted_by")
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


@login_required
def export_applicants(request, job_id):

    job = get_object_or_404(Job, pk=job_id)

    # ensure only recruiter who posted job can export
    if job.posted_by != request.user:
        return HttpResponseForbidden("You are not allowed to export this data.")

    applications = Application.objects.filter(
        job=job,
        status='accepted'
    ).select_related('user')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{job.title}_accepted_applicants.csv"'

    writer = csv.writer(response)

    writer.writerow([
        'Applicant Name',
        'Applied Date',
        'ATS Score'
    ])

    for app in applications:
        writer.writerow([
            app.user.username,
            app.applied_at.strftime("%d-%m-%Y %H:%M"),
            app.score
        ])

    return response

@login_required
def candidate_profile_edit(request):

    profile = request.user.profile

    if request.method == "POST":
        form = CandidateProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
            user=request.user
        )

        if form.is_valid():
            profile = form.save(commit=False)

            # 🔥 SAVE CUSTOM FIELDS
            profile.education = request.POST.get('education', '')
            profile.skills = request.POST.get('skills', '')
            profile.experience = request.POST.get('experience', '')

            profile.save()

            # 🔥 NEW: update email on the User model
            new_email = request.POST.get('email', '').strip()
            if new_email and new_email != request.user.email:
                request.user.email = new_email
                request.user.save()

            return redirect('resumes:candidate_dashboard')

    else:
        # ✅ THIS WAS MISSING
        form = CandidateProfileForm(
            instance=profile,
            user=request.user
        )

    return render(
        request,
        'resumes/candidate_profile_form.html',
        {'form': form}
    )
    


@login_required
@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('login')