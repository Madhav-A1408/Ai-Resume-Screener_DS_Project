from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from resumes.views import role_redirect
from resumes import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', lambda request: redirect('resumes:job_list')),

    # resumes app
    path('resumes/', include(('resumes.urls','resumes'), namespace='resumes')),
    path('role-redirect/', role_redirect, name='role_redirect'),
    path('accounts/password_reset/', views.password_reset, name='password_reset'),

    # EXPLICIT login/logout routes you want templates to use
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # Use POST logout (recommended) or next_page redirect
   path('logout/', views.logout_view, name='logout'),
    path(
    'admin-logout/',
    auth_views.LogoutView.as_view(next_page='/admin/login/'),
    name='admin_logout'
),


    # Keep the default auth URLs under /accounts/ for password reset etc.
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
