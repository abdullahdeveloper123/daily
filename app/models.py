from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import os
from django.utils import timezone

class ApplicationForms(models.Model):
    name = models.CharField(max_length=255)  # User's name
    email = models.EmailField(unique=True)  # User's email, must be unique
    hashed_password = models.CharField(max_length=255)  # User's hashed password
    phone = models.CharField(max_length=20)  # User's phone number
    ip_address =  models.CharField(max_length=255)  # User's IP address
    country = models.CharField(max_length=100)  # User's country
    city = models.CharField(max_length=100)  # User's city
    address =  models.CharField(max_length=100, null=True)  # User's city
    date =  models.DateField(auto_now_add=True, null=True)  #  Subbmission Date
    time =  models.TimeField(auto_now_add=True, null=True)  # Submission time

class Users(models.Model):
         email = models.EmailField(unique=True)  # User's email, must be unique
         name = models.CharField(max_length=255)  # User's name
         hashed_password = models.CharField(max_length=255)  # User's hashed password


# Custom User Account Manager
class UserAccountManager(BaseUserManager):
    # creating custom user
    def create_user(self, email, username, password=None, **extra_fields):
        # Required Fields
        if not email:
            raise ValueError("You must have a valid email address.")
        if not username:
            raise ValueError("You must have a valid username.")
        user = self.model( 
            email=self.normalize_email(email),
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    # creating super user
    def create_superuser(self, email, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password
        )
        # privaligies for super user
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

# Custom User Model
class CustomUser(AbstractBaseUser):
    # Table Columns
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True)
    birthday = models.DateField()
    phone_number1 = models.CharField(max_length=30)
    phone_number2 = models.CharField(max_length=30, null=True, blank=True)
    Driving_license_id = models.CharField(max_length=30)
    driving_license_expiry_date = models.DateField()
    passport_id = models.CharField(max_length=30)
    passport_expiry_date = models.DateField()
    home_address = models.CharField(max_length=100)
    work_office_address = models.CharField(max_length=100)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now = True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)
    
    # Abstract User would be a => Custom User
    objects = UserAccountManager()
    
    # Email is required for authentication stuff
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] # another required field is username
    
    def __str__(self):
        return self.email
    # Perms for super user
    def has_perm(self, perm, obj=None):
        return True
    def has_module_perms(self, app_label):
        return True

    
# Regsiter User`s Uploaded Images
class UserImages(models.Model):
    user = models.ForeignKey(CustomUser, related_name='user_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
      return F"image{self.user.first_name} {self.user.last_name}"

# Register User`s Uploaded Videos
class UserVideos(models.Model):
   user = models.ForeignKey(CustomUser, related_name='user_videos', on_delete=models.CASCADE)
   video = models.FileField(upload_to="videos/")
   uploaded_at = models.DateTimeField(auto_now_add=True)

   def __str__(self):
        return f"Video{self.user.first_name} {self.user.last_name}"

# Registered User`s Uploaded Documents
class UserDocuments(models.Model):
    user = models.ForeignKey(CustomUser, related_name='user_documents', on_delete=models.CASCADE)
    document = models.FileField(upload_to='user_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document{self.user.first_name} {self.user.last_name}"

# <<< Regsiteration Model ends Here >>>