from django import forms 
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate

from .models import CustomUser

# Registeration Form
class RegisterationForm(UserCreationForm):
    # Meta data from User
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "birthday", "email",
                   "phone_number1", "phone_number2", "Driving_license_id",
                   "driving_license_expiry_date", "passport_id", "passport_expiry_date",
                   "home_address", "work_office_address", "password1", "password2"
                 ]
        # Form saving and commits
        def save(self, commit=True):
            user = super().save(commit=False)
            user.set_password(self.cleaned_data['password1']) # set password for user
            if commit:
                user.save()
            return user

    
