"""
API views for the users app.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from .models import User, UserProfile, UserSession, UserActivity, UserQuota, UserPermission
from shared.utils import APIResponse, LoggingHelper, ValidationHelper, SecurityHelper
from shared.models import AuditLog
import uuid


@api_view(['POST'])
def register_user(request):
    """Register a new user."""
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return APIResponse.error(f"Missing required field: {field}", status_code=400)
        
        # Check if user already exists
        if User.objects.filter(email=data['email']).exists():
            return APIResponse.error("User with this email already exists", status_code=400)
        
        # Create user
        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            username=data['email']  # Use email as username
        )
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Log the registration
        LoggingHelper.log_info(f"User registered", {
            "user_id": str(user.id),
            "email": user.email
        })
        
        # Create audit log
        AuditLog.objects.create(
            event_type='user_action',
            event_name='user_registered',
            user_id=user.id,
            details={"email": user.email}
        )
        
        return APIResponse.success({
            "message": "User registered successfully",
            "user_id": str(user.id)
        }, status_code=201)
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to register user", e)
        return APIResponse.error(f"Failed to register user: {str(e)}", status_code=500)


@api_view(['POST'])
def login_user(request):
    """Authenticate and login a user."""
    try:
        data = request.data
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return APIResponse.error("Email and password are required", status_code=400)
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            LoggingHelper.log_warning(f"Failed login attempt", {"email": email})
            return APIResponse.error("Invalid credentials", status_code=401)
        
        if not user.is_active:
            return APIResponse.error("Account is deactivated", status_code=401)
        
        # Login user
        login(request, user)
        
        # Create session
        session_token = SecurityHelper.generate_secure_token()
        UserSession.objects.create(
            user=user,
            session_token=session_token,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            expires_at=timezone.now() + timezone.timedelta(hours=24)
        )
        
        # Update user activity
        user.update_last_activity(request.META.get('REMOTE_ADDR'))
        
        # Log user activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            description='User logged in',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Log the login
        LoggingHelper.log_info(f"User logged in", {
            "user_id": str(user.id),
            "email": user.email
        })
        
        return APIResponse.success({
            "message": "Login successful",
            "user_id": str(user.id),
            "session_token": session_token,
            "expires_at": timezone.now() + timezone.timedelta(hours=24)
        })
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to login user", e)
        return APIResponse.error(f"Failed to login user: {str(e)}", status_code=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Logout a user and invalidate session."""
    try:
        user = request.user
        
        # Get session token from request
        session_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        
        # Deactivate session
        if session_token:
            UserSession.objects.filter(
                user=user,
                session_token=session_token
            ).update(is_active=False)
        
        # Log user activity
        UserActivity.objects.create(
            user=user,
            activity_type='logout',
            description='User logged out',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Logout user
        logout(request)
        
        LoggingHelper.log_info(f"User logged out", {
            "user_id": str(user.id),
            "email": user.email
        })
        
        return APIResponse.success({"message": "Logout successful"})
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to logout user", e)
        return APIResponse.error(f"Failed to logout user: {str(e)}", status_code=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """Get current user's profile."""
    try:
        user = request.user
        
        # Get or create profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        profile_data = {
            "user_id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "company": user.company,
            "job_title": user.job_title,
            "timezone": user.timezone,
            "language": user.language,
            "is_verified": user.is_verified,
            "last_activity": user.last_activity,
            "profile_completion_percentage": profile.profile_completion_percentage,
            "bio": profile.bio,
            "skills": profile.skills,
            "experience_years": profile.experience_years,
            "education": profile.education,
            "certifications": profile.certifications
        }
        
        LoggingHelper.log_info(f"User profile requested", {
            "user_id": str(user.id)
        })
        
        return APIResponse.success(profile_data)
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to get user profile", e)
        return APIResponse.error(f"Failed to get user profile: {str(e)}", status_code=500)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """Update current user's profile."""
    try:
        user = request.user
        data = request.data
        
        # Update user fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'phone_number' in data:
            user.phone_number = data['phone_number']
        if 'company' in data:
            user.company = data['company']
        if 'job_title' in data:
            user.job_title = data['job_title']
        if 'timezone' in data:
            user.timezone = data['timezone']
        if 'language' in data:
            user.language = data['language']
        
        user.save()
        
        # Update profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        if 'bio' in data:
            profile.bio = data['bio']
        if 'skills' in data:
            profile.skills = data['skills']
        if 'experience_years' in data:
            profile.experience_years = data['experience_years']
        if 'education' in data:
            profile.education = data['education']
        if 'certifications' in data:
            profile.certifications = data['certifications']
        
        profile.save()
        
        # Recalculate completion percentage
        profile.calculate_completion_percentage()
        
        # Log user activity
        UserActivity.objects.create(
            user=user,
            activity_type='profile_update',
            description='User profile updated',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        LoggingHelper.log_info(f"User profile updated", {
            "user_id": str(user.id)
        })
        
        return APIResponse.success({"message": "Profile updated successfully"})
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to update user profile", e)
        return APIResponse.error(f"Failed to update user profile: {str(e)}", status_code=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_quota(request):
    """Get current user's quota usage."""
    try:
        user = request.user
        
        # Get current quotas
        quotas = UserQuota.objects.filter(user=user).order_by('-period_start')
        
        quota_data = []
        for quota in quotas:
            quota_info = {
                "quota_type": quota.quota_type,
                "limit": quota.limit,
                "used": quota.used,
                "remaining": quota.remaining,
                "usage_percentage": quota.usage_percentage,
                "period_start": quota.period_start,
                "period_end": quota.period_end
            }
            quota_data.append(quota_info)
        
        LoggingHelper.log_info(f"User quota requested", {
            "user_id": str(user.id)
        })
        
        return APIResponse.success({"quotas": quota_data})
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to get user quota", e)
        return APIResponse.error(f"Failed to get user quota: {str(e)}", status_code=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_activity(request):
    """Get current user's activity history."""
    try:
        user = request.user
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        
        # Get user activities
        activities = UserActivity.objects.filter(user=user).order_by('-created_at')
        
        total_count = activities.count()
        activities = activities[offset:offset + limit]
        
        activity_data = []
        for activity in activities:
            activity_info = {
                "id": str(activity.id),
                "activity_type": activity.activity_type,
                "description": activity.description,
                "created_at": activity.created_at,
                "ip_address": str(activity.ip_address) if activity.ip_address else None,
                "metadata": activity.metadata
            }
            activity_data.append(activity_info)
        
        response_data = {
            "activities": activity_data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
        LoggingHelper.log_info(f"User activity requested", {
            "user_id": str(user.id),
            "total_count": total_count
        })
        
        return APIResponse.success(response_data)
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to get user activity", e)
        return APIResponse.error(f"Failed to get user activity: {str(e)}", status_code=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_permissions(request):
    """Get current user's permissions."""
    try:
        user = request.user
        
        # Get user permissions
        permissions = UserPermission.objects.filter(user=user, is_granted=True)
        
        permission_data = []
        for permission in permissions:
            if permission.is_valid():
                permission_info = {
                    "permission_type": permission.permission_type,
                    "granted_at": permission.granted_at,
                    "expires_at": permission.expires_at,
                    "context": permission.context
                }
                permission_data.append(permission_info)
        
        LoggingHelper.log_info(f"User permissions requested", {
            "user_id": str(user.id),
            "permission_count": len(permission_data)
        })
        
        return APIResponse.success({"permissions": permission_data})
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to get user permissions", e)
        return APIResponse.error(f"Failed to get user permissions: {str(e)}", status_code=500)