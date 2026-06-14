# from django.contrib import admin
# from .models import Job, Profile, Application

# admin.site.register(Job)
# admin.site.register(Profile)
# admin.site.register(Application)
from django.contrib import admin
from .models import Job, Profile, Application


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'company')
    list_filter = ('role',)


admin.site.register(Job)
admin.site.register(Application)
admin.site.register(Profile, ProfileAdmin)