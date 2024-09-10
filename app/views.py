from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse
from django.contrib.auth.hashers import make_password,check_password
from .models import ApplicationForms, Users
import requests
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth import login
import hashlib
from .forms import RegisterationForm

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
    try:
        otp = random.randint(1000, 9999)
        return otp
    except Exception as e:
        print(f"Error generating OTP: {e}")
        return None


# Regenerate OTP
def regenerate_otp(request):
    try:
        otp = generate_otp()
        if otp is None:
            raise ValueError("Failed to generate OTP")

        email = request.session.get('otp_email')
        if not email:
            raise ValueError("Email not found in session")

        # Hash the OTP and store it in the session
        request.session['hashed_otp'] = hashlib.sha256(str(otp).encode()).hexdigest()

        # Send OTP via email
        send_otp_mail(email, otp)

        # Redirect to email verification page
        return redirect(reverse("email_verification"))

    except Exception as e:
        print(f"Error regenerating OTP: {e}")
        # You can add more meaningful error handling like logging, user notifications, etc.
        return redirect(reverse("error_page"))  # Example of redirecting to an error page

# Send OTP Email
def send_otp_mail(email, otp):
    try:
        subject = 'Your OTP Code'
        message = f'Your OTP code is {otp}. It is valid for 10 minutes.'
        email_from = settings.EMAIL_HOST_USER
        recipient = [email]

        # Send the email
        send_mail(subject, message, email_from, recipient)
        print(f"OTP sent to {email}")

    except Exception as e:
        print(f"Error sending OTP email: {e}")
        # Optionally log the error or notify the user
        return False

    return True

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
        try:
            # Get the reCAPTCHA response token from the POST request
            recaptcha_response = request.POST.get('g-recaptcha-response')

            # Verify reCAPTCHA
            if not verify_recaptcha(recaptcha_response):
                messages.error(request, 'Invalid reCAPTCHA. Please try again.')
                return render(request, 'authentication/applicationform.html', {'captcha_not_solved': True})

            # Extract form data
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            password = request.POST.get('password')

            # Validate required fields
            if not all([name, email, phone, address, password]):
                messages.error(request, 'All fields are required.')
                return render(request, 'authentication/applicationform.html')

            # Hash the password
            hashed_password = make_password(password)

            # Get the IP address of the registrant
            ip_address = get_client_ip(request)

            # Get location of user from POST request or IP API
            city = request.POST.get('city')
            country = request.POST.get('country')

            # Fallback to IP location if city or country not provided
            if not city or not country:
                city, country = get_location_from_ip(ip_address)

            # Generate OTP and send it to the client
            otp = generate_otp()
            if not otp:
                raise ValueError("Failed to generate OTP")

            # Send OTP email
            if not send_otp_mail(email, otp):
                messages.error(request, 'Failed to send OTP email. Please try again.')
                return render(request, 'authentication/applicationform.html')

            # Store OTP and form data in session
            request.session['hashed_otp'] = hashlib.sha256(str(otp).encode()).hexdigest()
            request.session['otp_email'] = email
            request.session.set_expiry(300)  # Session expiry in 5 minutes (300 seconds)

            # Store hashed form data in session for later use
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

        except Exception as e:
            # Log the error (optional) and display a user-friendly message
            print(f"Error processing application form: {e}")
            messages.error(request, 'There was an error processing your request. Please try again.')
            return render(request, 'authentication/applicationform.html')

    # Render the registration form for GET requests
    return render(request, 'authentication/applicationform.html')

def success_application_submission(request):
    return render(request, 'authentication/success_application_form.html')



# OTP Verification Handler
def otp_verification(request):
    if request.method == 'POST':
        try:
            # Combine the 4 OTP digits
            otp1 = request.POST.get('otp1')
            otp2 = request.POST.get('otp2')
            otp3 = request.POST.get('otp3')
            otp4 = request.POST.get('otp4')

            # Ensure all 4 digits are provided
            if not all([otp1, otp2, otp3, otp4]):
                messages.error(request, 'Please enter the complete OTP.')
                return render(request, 'authentication/otp.html', {"otp_incomplete": True})

            # Concatenate the OTP digits
            otp = otp1 + otp2 + otp3 + otp4

            # Get the stored hashed OTP from session
            stored_otp_hash = request.session.get('hashed_otp')
            if not stored_otp_hash:
                messages.error(request, 'Session expired. Please try again.')
                return redirect('applicationform')

            # Verify the entered OTP against the hashed OTP in session
            if hashlib.sha256(str(otp).encode()).hexdigest() == stored_otp_hash:
                form_data = request.session.get('form_data')
                
                # Ensure form data is available in session
                if form_data:
                    # Save the application data to the database
                    query = ApplicationForms(**form_data)
                    query.save()

                    # Clear session data after successful submission
                    del request.session['hashed_otp']
                    del request.session['form_data']
                    del request.session['otp_email']

                    # Redirect to success page
                    return redirect('success_application_submission')
                else:
                    messages.error(request, 'Session expired. Please fill the form again.')
                    return redirect('applicationform')
            else:
                # OTP does not match
                messages.error(request, 'Invalid OTP. Please try again.')
                return render(request, 'authentication/otp.html', {"otp_not_matched": True})
        except Exception as e:
            # Log the error (optional)
            print(f"Error during OTP verification: {e}")
            messages.error(request, 'An error occurred during OTP verification. Please try again.')
            return render(request, 'authentication/otp.html')
    
    # If the request method is GET
    elif request.method == 'GET':
        if request.session.get('hashed_otp'):
            # Render the OTP page if session data is valid
            return render(request, "authentication/otp.html")
        else:
            # Redirect back if no OTP session data
            messages.error(request, 'Session expired. Please fill the form again.')
            return redirect('applicationform')



# Register form view
def register(request):
    # if user is already authenticated
    user = request.user
    if user.is_authenticated:
        return HttpResponse(F"<h1> You are already authenticated as {user.email}.")
 
    context = {}
    
    # Post handeling
    if request.POST:
        form = RegisterationForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data['email']
            raw_password = form.cleaned_data['password1']
            account = authenticate(email=email, password=raw_password)
            #if account is not None:
                #login(request, account)
            #else:
                #Sprint("can`t directly log you in")
            return redirect("login") # Bro, set it to home page :)
        else: 
            context['registeration_form'] = form
            print("Form is invalid")

    return render(request, "authentication/register.html", context)

# Login Handler
def login(request):
    if request.method == 'POST':
        try:
            # Get the reCAPTCHA response token from the POST request
            recaptcha_response = request.POST.get('g-recaptcha-response')

            # Verify reCAPTCHA
            if not verify_recaptcha(recaptcha_response):
                messages.error(request, 'Invalid reCAPTCHA. Please try again.')
                return render(request, 'authentication/login.html', {'captcha_not_solved': True})

            # Get email and password from POST request
            email = request.POST.get('email')
            password = request.POST.get('password')

            # Ensure both email and password are provided
            if not email or not password:
                messages.error(request, 'Please provide both email and password.')
                return render(request, 'authentication/login.html')

            # Query the database for the user
            try:
                query = Users.objects.get(email=email)
            except Users.DoesNotExist:
                messages.error(request, 'Incorrect email or password. Please try again.')
                return render(request, 'authentication/login.html')

            # Check if the password matches the hashed password in the database
            if check_password(password, query.hashed_password):
                # User is authenticated successfully
                return HttpResponse('<h1>User is authorized</h1>')
            else:
                messages.error(request, 'Incorrect email or password. Please try again.')
                return render(request, 'authentication/login.html')

        except Exception as e:
            # Log the error and return a general error message
            print(f"Login error: {e}")
            messages.error(request, 'An error occurred. Please try again later.')
            return render(request, 'authentication/login.html')

    # Render the login page for GET requests
    return render(request, 'authentication/login.html')
            
 
def empolee_listing(request):
     return render(request, 'main/empolee_listing.html')

def home(request):
    # Render the home page (or any other appropriate page)
    return render(request, 'authentication/register.html')
