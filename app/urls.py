from django.urls import path 
from . import views


urlpatterns = [
    # Application routes
    path('apply/', views.applicationform, name='applicationform'),
    path('success_application_submission/', views.success_application_submission, name='success_application_submission'),
    path('email_verification/', views.otp_verification, name='email_verification'),
    path('regenerate_otp/', views.regenerate_otp, name='regenerate_otp'),

    
    # Authentication Routes
    path('login/', views.login, name='login'), 
    path('register/', views.register, name='register'), 

    # Main Pages Routes
    path('empolees/', views.empolee_listing, name="empolee_listing"),

    path('home/', views.home, name='home'),

]
