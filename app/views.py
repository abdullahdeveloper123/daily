from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse
from django.contrib.auth.hashers import make_password,check_password
from .models import ApplicationForms, Users
import requests
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import hashlib

# Utility function to get the client's IP address
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Function to get location using the ipapi service
def get_location_from_ip(ip_address):
    try:
        url = f'https://ipapi.co/{ip_address}/json/'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city')
            country = data.get('country_name')
            return city, country
    except Exception as e:
        print(f"Error retrieving location: {e}")
    return None, None

# Generate OTP from random numbers
def generate_otp():
    return random.randint(1000, 9999)

# Regenrate otp
def regenerate_otp(request):
    otp = generate_otp()
    email = request.session.get('otp_email')
    request.session['hashed_otp'] = hashlib.sha256(str(otp).encode()).hexdigest() 
    send_otp_mail(email, otp)
    return redirect(reverse("email_verification"))


# Send Otp Email
def send_otp_mail(email, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It is valid for 10 minutes.'
    email_from = settings.EMAIL_HOST_USER
    recipient = [email]
    send_mail(subject, message, email_from, recipient)

# Create reCAPTCHA results
def verify_recaptcha(response_token):
    url = 'https://www.google.com/recaptcha/api/siteverify'
    params = {
        'secret': settings.RECAPTCHA_SECRET_KEY,
        'response': response_token
    }
    response = requests.post(url, data=params)
    result = response.json()
    return result.get('success', False)

# Application Form Handler
def applicationform(request):
    if request.method == 'POST':
        # Get the reCAPTCHA response token from the POST request
        recaptcha_response = request.POST.get('g-recaptcha-response')

        # Verify reCAPTCHA
        if not verify_recaptcha(recaptcha_response):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, 'authentication/applicationform.html', {'captcha_not_solved':True})

        # Extract form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        password = request.POST.get('message')

        
        # Hash the password
        hashed_password = make_password(password)

        # Get the IP address of the registrant
        ip_address = get_client_ip(request)

        # Get location of user from POST request or ipapi
        city = request.POST.get('city')
        country = request.POST.get('country')

        if not city or not country:
            city, country = get_location_from_ip(ip_address)

        # Generate OTP and send to client
        otp = generate_otp()
        send_otp_mail(email, otp)

        # Store OTP in session with hashed form data
        request.session['hashed_otp'] = hashlib.sha256(str(otp).encode()).hexdigest()
        request.session['otp_email'] = email
        request.session.set_expiry(300)
        request.session['form_data'] = {
            'name': name,
            'email': email,
            'phone': phone,
            'hashed_password': hashed_password,
            'ip_address': ip_address,
            'country': country,
            'city': city,
            'address': address
        }

        return redirect('email_verification')

    # Render the registration form for GET requests
    return render(request, 'authentication/applicationform.html')

def success_application_submission(request):
    return render(request, 'authentication/success_application_form.html')


# Registeration Handler
def register(request):
     if request.method == 'POST':
         name = request.POST['name']
         email = request.POST['name']
         password= request.POST['password'] 
         hashed_password = make_password(password)   
         query = Users(name=name,email=email,hashed_password=hashed_password)
         query.save()
         return HttpResponse("<h1>user registered successfully</h1>")
     else:
         return render(request, 'authentication/register.html')

# Login Handler
def login(request):
    if request.method == 'POST':
        # Get the reCAPTCHA response token from the POST request
        recaptcha_response = request.POST.get('g-recaptcha-response')

        # Verify reCAPTCHA
        if not verify_recaptcha(recaptcha_response):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, 'authentication/login.html', {'captcha_not_solved':True})


        email = request.POST['email']
        password = request.POST['password']
        query = Users.objects.get(email=email)
        # Authorizing email 
        if query: 
            # Authorizing User password
            if check_password(password, query.hashed_password):
              return HttpResponse('<h1>User is authorized</h1>')
            else: 
                 return HttpResponse('<h1>Incorrect Username or password</h1>')
        else:
          return HttpResponse('<h1>User not Found</h1>') 
     
    else: return render(request, 'authentication/login.html')
            



# Verifying Otp 
def otp_verification(request):
    if request.method == 'POST':
        otp1 = request.POST.get('otp1')
        otp2 = request.POST.get('otp2')
        otp3 = request.POST.get('otp3')
        otp4 = request.POST.get('otp4')
        otp = otp1+otp2+otp3+otp4
        stored_otp_hash = request.session.get('hashed_otp')
        if hashlib.sha256(str(otp).encode()).hexdigest() == stored_otp_hash:
            form_data = request.session.get('form_data')
            if form_data:
                query = ApplicationForms(**form_data)
                query.save()
                return redirect('success_application_submission')
            else:
                return HttpResponse('<h1>Session expired. Please try again.</h1>')
        else:
            return render(request, 'authentication/otp.html', {"otp_not_matched" : True})
    else:
        if request.session.get('hashed_otp'):  
          return render(request, "authentication/otp.html")
        else: return redirect(request.META.get('HTTP_REFERER'))


def home(request):
    # Render the home page (or any other appropriate page)
    return render(request, 'authentication/register.html')
