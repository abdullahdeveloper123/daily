from django.shortcuts import render, HttpResponse, redirect
from django.http import HttpResponse, HttpResponseBadRequest
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
from django.core.files.storage import default_storage
from datetime import datetime
import os


 # Extract dates and ensure they are in the correct format
def parse_date(date_str):
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None

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

def register(request):
    if request.method == 'POST':
        # Get the reCAPTCHA response token from the POST request
        recaptcha_response = request.POST.get('g-recaptcha-response')

        # Verify reCAPTCHA
        if not verify_recaptcha(recaptcha_response):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, 'authentication/register.html', {'captcha_not_solved': True})

        fname = request.POST.get('first_name', '').strip()
        lname = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        birthday = parse_date(request.POST.get('birthday', ''))
        driving_date = parse_date(request.POST.get('driving_license_expiry_date', ''))
        passport_date = parse_date(request.POST.get('passport_expiry_date', ''))
        phone1 = request.POST.get('phone_number1', '').strip()
        phone2 = request.POST.get('phone_number2', '').strip()
        driving_id = request.POST.get('Driving_license_id', '').strip()
        passport_id = request.POST.get('passport_id', '').strip()
        office_address = request.POST.get('work_office_address', '').strip()
        home_address = request.POST.get('home_address', '').strip()
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()

        # Validate passwords
        if password1 != password2:
            return HttpResponseBadRequest('<h1>Passwords do not match</h1>')

        if not email or not password1:
            return HttpResponseBadRequest('<h1>Email and Password are required</h1>')

        # Check if the user already exists
        if Users.objects.filter(email=email).exists():
            return render(request, 'authentication/register.html', {'user_found': True})

        # Define directory paths for different file types
        IMAGE_DIR = os.path.join('media/images', email)
        VIDEO_DIR = os.path.join('media/videos', email)
        DOCUMENT_DIR = os.path.join('media/documents', email)

        # Create directories if they do not exist
        try:
            os.makedirs(IMAGE_DIR, exist_ok=True)
            os.makedirs(VIDEO_DIR, exist_ok=True)
            os.makedirs(DOCUMENT_DIR, exist_ok=True)
        except Exception as e:
            return HttpResponseBadRequest(f'<h1>Error creating directories: {e}</h1>')

        # Lists to hold file names
        images_list = []
        videos_list = []
        documents_list = []

        try:
            # Handle images
            image_files = request.FILES.getlist('images')
            if len(image_files) > 3:
                return render(request, 'authentication/register.html', {'images_exceed': True})
            for file in image_files:
                if not file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    return HttpResponseBadRequest('<h1>Invalid image file type</h1>')
                file_name = file.name
                file_path = os.path.join(IMAGE_DIR, file_name)
                with default_storage.open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                images_list.append(file_name)

            # Handle videos
            video_files = request.FILES.getlist('videos')
            if len(video_files) > 3:
                return render(request, 'authentication/register.html', {'images_exceed': True})
            for file in video_files:
                if not file.name.lower().endswith(('.mp4', '.avi', '.mov')):
                    return HttpResponseBadRequest('<h1>Invalid video file type</h1>')
                file_name = file.name
                file_path = os.path.join(VIDEO_DIR, file_name)
                with default_storage.open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                videos_list.append(file_name)

            # Handle documents
            document_files = request.FILES.getlist('documents')
            if len(document_files) > 3:
                return render(request, 'authentication/register.html', {'documents_exceed': True})
            for file in document_files:
                if not file.name.lower().endswith(('.pdf', '.doc', '.docx', '.txt')):
                    return HttpResponseBadRequest('<h1>Invalid document file type</h1>')
                file_name = file.name
                file_path = os.path.join(DOCUMENT_DIR, file_name)
                with default_storage.open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                documents_list.append(file_name)

        except Exception as e:
            return HttpResponseBadRequest(f'<h1>Error handling files: {e}</h1>')

        # Create and save the user instance
        try:
            new_user = Users(
                first_name=fname,
                last_name=lname,
                email=email,
                password1=make_password(password1),
                password2=make_password(password2),
                birthday=birthday,
                phone_number1=phone1,
                phone_number2=phone2,
                Driving_license_id=driving_id,
                driving_license_expiry_date=driving_date,
                passport_id=passport_id,
                passport_expiry_date=passport_date,
                home_address=home_address,
                work_office_address=office_address,
                image=images_list,
                video=videos_list,
                document=documents_list
            )
            new_user.save()
        except Exception as e:
            return HttpResponseBadRequest(f'<h1>Error saving user data: {e}</h1>')

        return HttpResponse('<h1>Registration Successful</h1>')

    else:
        return render(request, 'authentication/register.html')

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
                return render(request, 'authentication/login.html', {'userNotFound':True})

            # Check if the password matches the hashed password in the database
            if check_password(password, query.password1):
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
            
 
#  employees listing page
def empolee_listing(request):
     return render(request, 'main/empolee_listing.html')


# employee Profile Visitor View
def employee_profile(request):
     return render(request, 'main/empolee_profile.html')


def home(request):
    # Render the home page (or any other appropriate page)
    return render(request, 'authentication/register.html')
