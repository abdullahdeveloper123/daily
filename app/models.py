from django.db import models

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


