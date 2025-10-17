"""
Shared utilities and common functions for the CV Evaluation system.
These utilities are designed to be used across multiple microservices.
"""

import json
import logging
import uuid
from typing import Any, Dict, Optional
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.utils import timezone


logger = logging.getLogger(__name__)


class APIResponse:
    """Standardized API response helper."""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> JsonResponse:
        """Create a successful API response."""
        response_data = {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": timezone.now().isoformat()
        }
        return JsonResponse(response_data, status=status_code, encoder=DjangoJSONEncoder)
    
    @staticmethod
    def error(message: str = "Error", errors: Dict = None, status_code: int = 400) -> JsonResponse:
        """Create an error API response."""
        response_data = {
            "success": False,
            "message": message,
            "errors": errors or {},
            "timestamp": timezone.now().isoformat()
        }
        return JsonResponse(response_data, status=status_code, encoder=DjangoJSONEncoder)


class LoggingHelper:
    """Centralized logging helper."""
    
    @staticmethod
    def log_info(message: str, extra_data: Dict = None, user_id: str = None):
        """Log info message with structured data."""
        log_data = {
            "message": message,
            "level": "INFO",
            "timestamp": timezone.now().isoformat(),
            "user_id": user_id,
            "extra_data": extra_data or {}
        }
        logger.info(json.dumps(log_data, cls=DjangoJSONEncoder))
    
    @staticmethod
    def log_error(message: str, exception: Exception = None, extra_data: Dict = None, user_id: str = None):
        """Log error message with structured data."""
        log_data = {
            "message": message,
            "level": "ERROR",
            "timestamp": timezone.now().isoformat(),
            "user_id": user_id,
            "exception": str(exception) if exception else None,
            "extra_data": extra_data or {}
        }
        logger.error(json.dumps(log_data, cls=DjangoJSONEncoder))
    
    @staticmethod
    def log_warning(message: str, extra_data: Dict = None, user_id: str = None):
        """Log warning message with structured data."""
        log_data = {
            "message": message,
            "level": "WARNING",
            "timestamp": timezone.now().isoformat(),
            "user_id": user_id,
            "extra_data": extra_data or {}
        }
        logger.warning(json.dumps(log_data, cls=DjangoJSONEncoder))


class ValidationHelper:
    """Common validation utilities."""
    
    @staticmethod
    def is_valid_uuid(uuid_string: str) -> bool:
        """Check if a string is a valid UUID."""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_file_type(filename: str, allowed_extensions: list) -> bool:
        """Validate file extension."""
        if not filename:
            return False
        return any(filename.lower().endswith(ext.lower()) for ext in allowed_extensions)
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int) -> bool:
        """Validate file size."""
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes


class SecurityHelper:
    """Security-related utilities."""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        import re
        # Remove or replace dangerous characters
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        # Remove multiple consecutive underscores
        filename = re.sub(r'_+', '_', filename)
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        return filename
    
    @staticmethod
    def generate_secure_token() -> str:
        """Generate a secure random token."""
        import secrets
        return secrets.token_urlsafe(32)


class HealthCheckHelper:
    """Health check utilities."""
    
    @staticmethod
    def check_database_health() -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {"status": "healthy", "response_time_ms": 0}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    def check_redis_health() -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            import redis
            import time
            start_time = time.time()
            
            r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
            r.ping()
            
            response_time = (time.time() - start_time) * 1000
            return {"status": "healthy", "response_time_ms": response_time}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    def check_llm_health() -> Dict[str, Any]:
        """Check LLM service connectivity."""
        try:
            import time
            from openai import OpenAI
            
            start_time = time.time()
            client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=5.0)
            # Simple test call
            client.models.list()
            
            response_time = (time.time() - start_time) * 1000
            return {"status": "healthy", "response_time_ms": response_time}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


class ConfigHelper:
    """Configuration management utilities."""
    
    @staticmethod
    def get_config(key: str, default: Any = None) -> Any:
        """Get configuration value."""
        try:
            from .models import SystemConfig
            config = SystemConfig.objects.get(key=key, is_active=True)
            return config.value
        except SystemConfig.DoesNotExist:
            return default
    
    @staticmethod
    def set_config(key: str, value: str, description: str = "") -> bool:
        """Set configuration value."""
        try:
            from .models import SystemConfig
            config, created = SystemConfig.objects.get_or_create(
                key=key,
                defaults={'value': value, 'description': description}
            )
            if not created:
                config.value = value
                config.description = description
                config.save()
            return True
        except Exception:
            return False


class MicroserviceHelper:
    """Utilities for microservice communication."""
    
    @staticmethod
    def create_service_url(service_name: str, endpoint: str = "") -> str:
        """Create service URL for inter-service communication."""
        base_url = getattr(settings, f'{service_name.upper()}_SERVICE_URL', f'http://{service_name}:8000')
        return f"{base_url}/{endpoint.lstrip('/')}" if endpoint else base_url
    
    @staticmethod
    def make_service_request(service_name: str, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Make a request to another microservice."""
        import requests
        
        url = MicroserviceHelper.create_service_url(service_name, endpoint)
        headers = {
            'Content-Type': 'application/json',
            'X-Service-Name': 'cv-evaluation-api'
        }
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            LoggingHelper.log_error(f"Service request failed: {service_name}/{endpoint}", e)
            return {"error": str(e)}


class EventPublisher:
    """Event publishing for microservice communication."""
    
    @staticmethod
    def publish_event(event_type: str, data: Dict, user_id: str = None):
        """Publish an event to the event bus."""
        try:
            from .models import AuditLog
            
            AuditLog.objects.create(
                event_type='system_event',
                event_name=event_type,
                user_id=user_id,
                details=data
            )
            
            # Here you could also publish to Redis, RabbitMQ, etc.
            LoggingHelper.log_info(f"Event published: {event_type}", data, user_id)
        except Exception as e:
            LoggingHelper.log_error(f"Failed to publish event: {event_type}", e)
