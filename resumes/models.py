from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from ckeditor.fields import RichTextField
from datetime import timedelta
class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('candidate', 'Candidate'),
        ('recruiter', 'Recruiter'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate')
    company = models.CharField(max_length=255, blank=True)
    
    # Candidate fields
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)

    education = models.TextField(blank=True)

    skills = models.CharField(max_length=500, blank=True)
    experience = models.TextField(blank=True)
    
    projects = models.TextField(blank=True)
    
    languages = models.CharField(max_length=200, blank=True)

    profile_summary = models.TextField(blank=True)

    resume = models.FileField(upload_to='candidate_resumes/',blank=True,null=True)

    # NEW fields for recruiter company details
    company_website = models.URLField(max_length=255, blank=True)
    company_phone = models.CharField(max_length=30, blank=True)
    company_address = models.TextField(blank=True)
    company_description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Job(models.Model):
    # existing fields...
    title = models.CharField(max_length=255)
    description = RichTextField(blank=True)
    company = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    # new field: comma-separated skill keywords
    application_deadline = models.DateField(null=True, blank=True)
    skills = models.CharField(max_length=512, blank=True, help_text="Comma-separated skills, e.g. Python, Django, SQL")
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='posted_jobs')
    created_at = models.DateTimeField(default=timezone.now)

    def get_skills_list(self):
        """Return normalized list of skills from the comma-separated field."""
        if not self.skills:
            return []
        # split on comma, strip whitespace, lower-case
        return [s.strip().lower() for s in self.skills.split(',') if s.strip()]

class Application(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    resume_text = models.TextField(blank=True)
    resume_file = models.FileField(upload_to='resumes_files/', null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    class Meta:
        unique_together = ('user', 'job')
    def __str__(self):
        return f"{self.user.username} -> {self.job.title}"
    
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=1)
