"""
User management models for the CV Evaluation system.
This app handles all user-related operations and can be split into a separate microservice.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from shared.models import BaseModel


class User(AbstractUser):
    """Extended user model with additional fields."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    
    # User profile information
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    
    # User preferences
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    
    # Account status
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=255, blank=True)
    verification_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # API access
    api_key = models.CharField(max_length=255, blank=True, unique=True)
    api_quota_daily = models.IntegerField(default=1000)
    api_quota_monthly = models.IntegerField(default=30000)
    
    class Meta:
        db_table = 'users_user'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    def update_last_activity(self, ip_address=None):
        """Update last activity timestamp."""
        self.last_activity = timezone.now()
        if ip_address:
            self.last_login_ip = ip_address
        self.save(update_fields=['last_activity', 'last_login_ip'])


class UserProfile(BaseModel):
    """Extended user profile information."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Professional information
    bio = models.TextField(blank=True)
    skills = models.JSONField(default=list)
    experience_years = models.IntegerField(null=True, blank=True)
    education = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    
    # Preferences
    notification_preferences = models.JSONField(default=dict)
    privacy_settings = models.JSONField(default=dict)
    
    # Profile completion
    profile_completion_percentage = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'users_user_profile'
    
    def __str__(self):
        return f"Profile for {self.user.email}"
    
    def calculate_completion_percentage(self):
        """Calculate profile completion percentage."""
        fields = [
            self.user.first_name,
            self.user.last_name,
            self.user.company,
            self.user.job_title,
            self.bio,
            self.skills,
            self.experience_years,
        ]
        
        completed_fields = sum(1 for field in fields if field)
        total_fields = len(fields)
        
        percentage = (completed_fields / total_fields) * 100
        self.profile_completion_percentage = int(percentage)
        self.save(update_fields=['profile_completion_percentage'])
        return percentage


class UserSession(BaseModel):
    """User session tracking."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_token = models.CharField(max_length=255, unique=True)
    
    # Session information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_info = models.JSONField(default=dict)
    
    # Session status
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_user_session'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_token']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email} from {self.ip_address}"
    
    def is_expired(self):
        """Check if session is expired."""
        return timezone.now() > self.expires_at
    
    def extend_session(self, hours=24):
        """Extend session expiration."""
        self.expires_at = timezone.now() + timezone.timedelta(hours=hours)
        self.save(update_fields=['expires_at'])


class UserActivity(BaseModel):
    """User activity tracking."""
    
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('api_call', 'API Call'),
        ('file_upload', 'File Upload'),
        ('evaluation_request', 'Evaluation Request'),
        ('profile_update', 'Profile Update'),
        ('password_change', 'Password Change'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField()
    
    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'users_user_activity'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'activity_type', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} at {self.created_at}"


class UserQuota(BaseModel):
    """User quota tracking."""
    
    QUOTA_TYPES = [
        ('api_calls_daily', 'Daily API Calls'),
        ('api_calls_monthly', 'Monthly API Calls'),
        ('file_uploads_daily', 'Daily File Uploads'),
        ('evaluations_daily', 'Daily Evaluations'),
        ('storage_mb', 'Storage (MB)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotas')
    quota_type = models.CharField(max_length=50, choices=QUOTA_TYPES)
    
    # Quota limits
    limit = models.IntegerField()
    used = models.IntegerField(default=0)
    
    # Time period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    class Meta:
        db_table = 'users_user_quota'
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['user', 'quota_type', 'period_start']),
            models.Index(fields=['quota_type', 'period_start']),
        ]
        unique_together = ['user', 'quota_type', 'period_start']
    
    def __str__(self):
        return f"{self.user.email} - {self.quota_type}: {self.used}/{self.limit}"
    
    @property
    def remaining(self):
        """Calculate remaining quota."""
        return max(0, self.limit - self.used)
    
    @property
    def usage_percentage(self):
        """Calculate usage percentage."""
        if self.limit == 0:
            return 0
        return (self.used / self.limit) * 100
    
    def can_use(self, amount=1):
        """Check if user can use specified amount."""
        return self.remaining >= amount
    
    def use_quota(self, amount=1):
        """Use quota amount."""
        if self.can_use(amount):
            self.used += amount
            self.save(update_fields=['used'])
            return True
        return False


class UserPermission(BaseModel):
    """User permissions and roles."""
    
    PERMISSION_TYPES = [
        ('api_access', 'API Access'),
        ('admin_panel', 'Admin Panel'),
        ('user_management', 'User Management'),
        ('system_config', 'System Configuration'),
        ('analytics', 'Analytics Access'),
        ('bulk_operations', 'Bulk Operations'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permissions')
    permission_type = models.CharField(max_length=50, choices=PERMISSION_TYPES)
    is_granted = models.BooleanField(default=True)
    
    # Permission details
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Additional context
    context = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'users_user_permission'
        ordering = ['-granted_at']
        indexes = [
            models.Index(fields=['user', 'permission_type']),
            models.Index(fields=['permission_type', 'is_granted']),
        ]
        unique_together = ['user', 'permission_type']
    
    def __str__(self):
        return f"{self.user.email} - {self.permission_type} ({'Granted' if self.is_granted else 'Denied'})"
    
    def is_valid(self):
        """Check if permission is valid and not expired."""
        if not self.is_granted:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True