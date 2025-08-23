from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CustomerInvitation

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'user_type', 'is_approved', 'email_verified', 'is_active')
    list_filter = ('user_type', 'is_approved', 'email_verified', 'is_active', 'gender', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture', 'birthday', 'gender')}),
        ('User Type & Permissions', {'fields': ('user_type', 'parent_customer_id', 'is_approved', 'approved_by', 'approved_at')}),
        ('Status', {'fields': ('is_active', 'email_verified', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Groups', {'fields': ('groups',)}),
        ('User permissions', {'fields': ('user_permissions',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'password1', 'password2', 'user_type'),
        }),
    )

@admin.register(CustomerInvitation)
class CustomerInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'customer', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('email', 'customer__username', 'customer__email')
    readonly_fields = ('token', 'created_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Invitation Details', {'fields': ('email', 'customer')}),
        ('Token & Status', {'fields': ('token', 'is_used', 'expires_at')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )
