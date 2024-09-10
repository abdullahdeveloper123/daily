from django.contrib import admin
from .models import CustomUser, UserImages, UserVideos, UserDocuments

 # making a tubular in DB for image model
class UserImageInline(admin.TabularInline):
    model = UserImages
    extra = 1  # Number of empty forms to display

 # making a tubular in DB for image model
class UserDocumentInline(admin.TabularInline):
    model = UserDocuments
    extra = 1  # Number of empty forms to display

 # making a tubular in DB for image model
class UserVideoInline(admin.TabularInline):
    model = UserVideos
    extra = 1  # Number of empty forms to display

# Register custom user
@admin.register(CustomUser)
class UserRegistrationAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone_number1', 'phone_number2', 'passport_id', 'home_address')
    search_fields = ('first_name', 'last_name', 'email', 'passport_id', 'home_address')
    inlines = [UserImageInline, UserDocumentInline, UserVideoInline]  # Add inlines here

# Register User Images
@admin.register(UserImages)
class UserImageAdmin(admin.ModelAdmin):
    list_display = ('user', 'image', 'uploaded_at')
    search_fields = ()
    readonly_fields = ()  # Make uploaded_at read-only

# Register User Documents
@admin.register(UserDocuments)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document', 'uploaded_at')
    search_fields = ()
    readonly_fields = ()  # Make uploaded_at read-only

# Register User Videos
@admin.register(UserVideos)
class UserVideoAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'uploaded_at')
    search_fields = ()
    readonly_fields = ('uploaded_at',)  # Make uploaded_at read-only
