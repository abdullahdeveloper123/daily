from django.db import models
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
    # Table Columns
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    birthday = models.CharField(max_length=100)
    password1 = models.CharField(max_length=100, null=True)
    password2 = models.CharField(max_length=100, null=True)
    phone_number1 = models.CharField(max_length=100)
    phone_number2 = models.CharField(max_length=100, null=True, blank=True)
    Driving_license_id = models.CharField(max_length=100)
    driving_license_expiry_date = models.CharField(max_length=100)
    passport_id = models.CharField(max_length=100)
    passport_expiry_date = models.CharField(max_length=100, null=True)
    home_address = models.CharField(max_length=100)
    work_office_address = models.CharField(max_length=100)
    image = models.CharField(max_length=100)
    image_uploaded_at = models.CharField(max_length=100)
    video = models.CharField(max_length=100)
    video_uploaded_at = models.CharField(max_length=100)
    document = models.CharField(max_length=100)
    uploaded_at = models.CharField(max_length=100)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now = True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)
    