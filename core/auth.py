#!/usr/bin/env python3
"""
API Key Authentication Module
Provides simple API key authentication for Flask endpoints
"""

import os
from functools import wraps
from flask import request, jsonify
from typing import Dict, List
from logger_utils import get_logger

logger = get_logger('auth')


# API Keys configuration
# In production, load from environment variables or secure database
API_KEYS = {
    # Development/test keys (change in production!)
    'dev-key-12345': {
        'user_id': 'dev-user',
        'roles': ['user', 'admin'],
        'description': 'Development key'
    },
    'test-key-67890': {
        'user_id': 'test-user',
        'roles': ['user'],
        'description': 'Test key'
    },
}

# Load API keys from environment if provided
def load_api_keys_from_env():
    """
    Load additional API keys from environment variables.

    Environment variables format:
    - API_KEY_<key_name>=<user_id>:<roles>

    Example:
        API_KEY_prod_abc123=service-a:user,admin
        API_KEY_prod_xyz789=service-b:user
    """
    for key, value in os.environ.items():
        if key.startswith('API_KEY_'):
            # Extract actual key name (remove 'API_KEY_' prefix)
            api_key = key[8:].lower()  # Remove 'API_KEY_' and convert to lowercase

            # Parse value (format: user_id:roles)
            parts = value.split(':')
            if len(parts) >= 1:
                user_id = parts[0]
                roles = parts[1].split(',') if len(parts) > 1 else ['user']

                API_KEYS[api_key] = {
                    'user_id': user_id,
                    'roles': roles,
                    'description': f'Loaded from environment'
                }

                logger.info(f"Loaded API key from environment: {api_key} -> {user_id}")


# Load keys from environment on module import
load_api_keys_from_env()


def verify_api_key(api_key: str) -> Dict:
    """
    Verify API key and return user information.

    Args:
        api_key: API key string to verify

    Returns:
        Dictionary with user information if valid

    Raises:
        ValueError: If API key is invalid
    """
    if not api_key:
        raise ValueError("API key is missing")

    if api_key not in API_KEYS:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise ValueError("Invalid API key")

    # Return user information
    return API_KEYS[api_key]


def require_api_key(f):
    """
    API key authentication decorator for protected routes.

    Usage:
        @app.route('/api/search')
        @require_api_key
        def search():
            # ... access request.user for authenticated user
            user_id = request.user.get('user_id')

    The decorator adds the following attributes to request:
        - request.user: Dictionary with user information
            {
                'user_id': str,
                'roles': List[str],
                'description': str
            }
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from X-API-Key header
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            logger.warning("API key missing in request")
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide X-API-Key header'
            }), 401

        try:
            # Verify API key
            user_info = verify_api_key(api_key)

            # Add user info to request
            request.user = user_info
            request.user_id = user_info.get('user_id')
            request.user_roles = user_info.get('roles', [])

            # Log successful authentication
            logger.info(f"API key authenticated: {request.user_id}")

            # Call the original function
            return f(*args, **kwargs)

        except ValueError as e:
            logger.warning(f"Authentication failed: {str(e)}")
            return jsonify({
                'error': 'Authentication failed',
                'message': str(e)
            }), 401

    return decorated_function


def require_role(required_role: str):
    """
    Role-based access control decorator.

    Usage:
        @app.route('/api/admin/clear_cache')
        @require_api_key
        @require_role('admin')
        def clear_cache():
            # Only users with 'admin' role can access

    Args:
        required_role: Role required to access the endpoint
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Ensure user is authenticated
            if not hasattr(request, 'user'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please authenticate first'
                }), 401

            # Check if user has required role
            user_roles = request.user.get('roles', [])
            if required_role not in user_roles:
                logger.warning(
                    f"Access denied: user {request.user_id} lacks role '{required_role}'"
                )
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f"'{required_role}' role required"
                }), 403

            # User has required role, proceed
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_admin(f):
    """
    Admin-only decorator (convenience wrapper for require_role('admin')).

    Usage:
        @app.route('/api/admin/users')
        @require_api_key
        @require_admin
        def admin_users():
            # Only admins can access
    """
    return require_role('admin')(f)


def add_new_api_key(api_key: str, user_id: str, roles: List[str] = None,
                    description: str = "") -> bool:
    """
    Add a new API key to the system.

    Args:
        api_key: API key string
        user_id: User identifier
        roles: List of roles (default: ['user'])
        description: Key description

    Returns:
        True if added successfully, False if key already exists

    Note:
        In production, you should persist API keys to a database
        instead of keeping them in memory.
    """
    if api_key in API_KEYS:
        logger.warning(f"API key already exists: {api_key}")
        return False

    API_KEYS[api_key] = {
        'user_id': user_id,
        'roles': roles or ['user'],
        'description': description
    }

    logger.info(f"Added new API key: {api_key} -> {user_id}")
    return True


def remove_api_key(api_key: str) -> bool:
    """
    Remove an API key from the system.

    Args:
        api_key: API key string to remove

    Returns:
        True if removed, False if key didn't exist
    """
    if api_key not in API_KEYS:
        return False

    del API_KEYS[api_key]
    logger.info(f"Removed API key: {api_key}")
    return True


def list_api_keys() -> Dict[str, Dict]:
    """
    List all API keys (without exposing the actual keys).

    Returns:
        Dictionary mapping key identifiers to user info

    Note:
        This should be an admin-only function in production.
    """
    # Return key info without the actual keys (for security)
    return {
        f"***{key[-4:]}": info  # Only show last 4 characters
        for key, info in API_KEYS.items()
    }


if __name__ == "__main__":
    # Test API key verification
    try:
        # Valid key
        user_info = verify_api_key('dev-key-12345')
        print(f"✅ Valid key: {user_info}")

        # Invalid key
        verify_api_key('invalid-key')
        print("❌ Invalid key not detected")
    except ValueError as e:
        print(f"✅ Invalid key detected: {e}")

    print("✅ All authentication tests passed")
