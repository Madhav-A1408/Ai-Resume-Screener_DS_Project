from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from resumes.models import Job, Profile
from resumes.ml_model import build_dummy_model
class Command(BaseCommand):
    help = 'Seed sample users and jobs and build model'
    def handle(self, *args, **options):
        User.objects.filter(username__in=['admin','rec1','cand1']).delete()
        admin = User.objects.create_user('admin','admin@example.com','pass')
        Profile.objects.create(user=admin, role='admin')
        rec = User.objects.create_user('rec1','rec1@example.com','pass')
        Profile.objects.create(user=rec, role='recruiter', company='Acme Inc')
        cand = User.objects.create_user('cand1','cand1@example.com','pass')
        Profile.objects.create(user=cand, role='candidate')
        Job.objects.all().delete()
        Job.objects.create(title='Backend Dev',company='Acme',description='Python Django Developer',location='Remote',posted_by=rec)
        Job.objects.create(title='Data Scientist',company='DataCorp',description='ML Engineer',location='Bangalore',posted_by=rec)
        build_dummy_model()
        self.stdout.write(self.style.SUCCESS('Seeded users, jobs and model'))
