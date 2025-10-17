#!/usr/bin/env python
"""
Test runner script for the CV Evaluation API.
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner


def setup_django():
    """Set up Django for testing."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_evaluator.settings')
    django.setup()


def run_tests():
    """Run all tests."""
    setup_django()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run tests
    failures = test_runner.run_tests([
        'tests.test_api_endpoints',
        'tests.test_llm_evaluator', 
        'tests.test_rag_system',
        'tests.test_models',
        'tests.test_serializers',
        'tests.test_error_handling',
        'tests.test_scoring_logic'
    ])
    
    if failures:
        sys.exit(bool(failures))
    else:
        print("\n✅ All tests passed successfully!")
        return 0


if __name__ == '__main__':
    run_tests()
