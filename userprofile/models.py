from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import UserManager
from django.apps import apps
from django.contrib.auth.hashers import make_password

class UserProfileManager(UserManager):
    def create_user(self, email=None, password=None, **extra_fields):
        return super(UserProfileManager, self).create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        return super(UserProfileManager, self).create_superuser( email, password, **extra_fields)

    def _create_user(self,email, password, *args, **extra_fields):
        email = self.normalize_email(email)
        # GlobalUserModel = apps.get_model(self.model._meta.app_label, self.model._meta.object_name)
        # email = email
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

class UserProfile(AbstractUser):
    # name = models.CharField(max_length=100)
    # username = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    username = None#models.CharField(max_length=50, null=True)
    first_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # Add any additional fields or methods as needed

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserProfileManager()

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    @property
    def is_teacher(self):
        return self.role == self.TEACHER

    @property
    def is_student(self):
        return self.role == self.STUDENT
