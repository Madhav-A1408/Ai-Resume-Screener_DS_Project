from django.test import TestCase
from django.contrib.auth.models import User
from .models import Job, Application, Profile

class SmokeTests(TestCase):
    def test_roles_and_basic_pages(self):
        u = User.objects.create_user('cand','c@example.com','pass')
        Profile.objects.create(user=u, role='candidate')
        resp = self.client.get('/resumes/')
        self.assertEqual(resp.status_code, 200)
