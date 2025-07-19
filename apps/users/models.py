from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    department = models.ForeignKey('departments.Department', on_delete=models.SET_NULL, null=True, blank=True)
    # Additional fields can be added here as needed

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    # Additional profile fields can be added here

    def __str__(self):
        return self.user.username