from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path("password_reset", views.password_reset, name="password_reset"),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    path('job/<int:pk>/apply/', views.apply_job, name='apply_job'),
    path('signup/candidate/', views.signup_candidate, name='signup_candidate'),
    path('signup/recruiter/', views.signup_recruiter, name='signup_recruiter'),
    path('recruiter/dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('recruiter/job/create/', views.job_create, name='job_create'),
    path('recruiter/job/<int:pk>/applicants/', views.view_applicants, name='view_applicants'),
    path('my-applications/', views.candidate_dashboard, name='candidate_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('ml-score/<int:application_id>/', views.ml_score_view, name='ml_score'),
    path('ckeditor/', include('ckeditor_uploader.urls')),

    # resumes/urls.py (add)
path('recruiter/profile/', views.recruiter_profile, name='recruiter_profile'),
path('recruiter/profile/edit/', views.recruiter_profile_edit, name='recruiter_profile_edit'),
path('change-password/', views.change_password_view, name='change_password'),

path("applications/history/", views.application_history, name="application_history"),
path('recruiter/job/<int:pk>/applicants/', views.view_applicants, name='view_applicants'),
path('recruiter/application/<int:app_id>/set-status/', views.set_application_status, name='set_application_status'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
