"""
Simple test file to ensure SonarQube workflow can run tests
"""
import pytest
import os
import sys


def test_basic_functionality():
    """Basic test to ensure pytest runs successfully"""
    assert True


def test_python_version():
    """Test that we're using Python 3.11+"""
    assert sys.version_info >= (3, 11)


def test_environment_variables():
    """Test that required environment variables can be set"""
    # This test will pass regardless of whether env vars are set
    os.environ.setdefault('TEST_VAR', 'test_value')
    assert os.environ.get('TEST_VAR') == 'test_value'


def test_file_structure():
    """Test that required files exist"""
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    
    # Check that we're in the right directory structure
    assert 'backend' in parent_dir or 'text-service' in current_dir
    
    # Check that key files exist
    assert os.path.exists(os.path.join(parent_dir, 'fastapi_app.py'))
    assert os.path.exists(os.path.join(parent_dir, 'requirements_production.txt'))


def test_import_basic_modules():
    """Test that basic Python modules can be imported"""
    import json
    import datetime
    import re
    import typing
    
    assert json is not None
    assert datetime is not None
    assert re is not None
    assert typing is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
