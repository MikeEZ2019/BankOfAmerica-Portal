from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class UserProfile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, unique=True, on_delete='CASCADE')
    box_user_id = models.CharField(max_length=40, blank=True)
    box_folder_id = models.CharField(max_length=40, blank=True)
    
    # def create_user_profile(sender, instance, created, **kwargs):
    #     logging.debug("Trying to create the user profile")
    #     if created:
    #         UserProfile.objects.create(user=instance)

class LoanApplication(models.Model):
	application_id = models.AutoField(primary_key=True)
	applicant = models.ForeignKey(User, on_delete='CASCADE')
	application_file_id = models.CharField(max_length=20)
	SUBMITTED = 'SUB'
	PENDING = 'PEND'
	APPROVED = 'APP'
	COMPLETE = 'COMP'
	status_choices = [(SUBMITTED, 'Submitted'), (PENDING, 'Pending'), (APPROVED, 'Approved'), (COMPLETE, 'Complete')]
	status = models.CharField(max_length=20, choices=status_choices, default=SUBMITTED)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def create_application(self): 
		self.created_at = timezone.now()

	def set_readable_status(self):
		if status == 'SUB':
			return "Submitted"
		else:
			return "Oops"