"""
URL routing for the users app.
"""

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.register_user, name='register'),
    path('auth/login/', views.login_user, name='login'),
    path('auth/logout/', views.logout_user, name='logout'),
    
    # User profile management
    path('profile/', views.get_user_profile, name='get_profile'),
    path('profile/update/', views.update_user_profile, name='update_profile'),
    
    # User quota and activity
    path('quota/', views.get_user_quota, name='get_quota'),
    path('activity/', views.get_user_activity, name='get_activity'),
    path('permissions/', views.get_user_permissions, name='get_permissions'),
]
