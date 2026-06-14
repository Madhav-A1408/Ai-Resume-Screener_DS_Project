from django.contrib.auth.signals import user_logged_in
from django.contrib import messages

def login_success_message(sender, request, user, **kwargs):
    messages.success(request, "Logged in successfully!")

user_logged_in.connect(login_success_message)