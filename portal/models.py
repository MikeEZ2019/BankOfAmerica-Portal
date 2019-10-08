from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, on_delete='CASCADE')
    box_user_id = models.CharField(max_length=40, blank=True)
    box_folder_id = models.CharField(max_length=40, blank=True)
    
    def create_user_profile(sender, instance, created, **kwargs):
        logging.debug("Trying to create the user profile")
        if created:
            UserProfile.objects.create(user=instance)