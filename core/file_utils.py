#!/usr/bin/env python3
"""
Safe file operations utility module
Prevents path traversal attacks and implements secure file handling
"""

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from logger_utils import get_logger

logger = get_logger('file_utils')


class PathTraversalError(ValueError):
    """Raised when path traversal attempt is detected"""
    pass


def safe_path_join(base_dir: str, user_path: str) -> str:
    """
    Safely join paths, preventing directory traversal attacks.

    Args:
        base_dir: Base directory (must be absolute path)
        user_path: User-supplied path component

    Returns:
        Absolute, safe path within base_dir

    Raises:
        PathTraversalError: If user_path tries to escape base_dir
        ValueError: If inputs are invalid

    Example:
        >>> safe_path_join('/app/data', 'file.txt')
        '/app/data/file.txt'
        >>> safe_path_join('/app/data', '../etc/passwd')
        PathTraversalError: Path traversal attempt detected
    """
    # Validate inputs
    if not base_dir or not user_path:
        raise ValueError("base_dir and user_path cannot be empty")

    # Resolve to absolute paths
    base = Path(base_dir).resolve()
    target = (base / user_path).resolve()

    # Ensure target is within base directory
    try:
        # Check if target is a subdirectory of base
        target.relative_to(base)
    except ValueError:
        raise PathTraversalError(
            f"Path traversal attempt detected: {user_path} tries to escape {base_dir}"
        )

    return str(target)


def safe_filename(filename: str) -> bool:
    """
    Validate filename is safe (no path traversal or dangerous characters).

    Args:
        filename: Filename to validate

    Returns:
        True if filename is safe, False otherwise

    Safe filenames:
        - Only contain alphanumeric, hyphens, underscores, spaces, dots
        - Don't start with dot (hidden files)
        - Don't contain path separators
        - Don't contain special characters (< > : " | ? *)

    Examples:
        >>> safe_filename('file.txt')
        True
        >>> safe_filename('../../../etc/passwd')
        False
        >>> safe_filename('file<script>.txt')
        False
    """
    if not filename or len(filename) > 255:
        return False

    # Reject path traversal patterns
    if '..' in filename or filename.startswith(('/', '\\')):
        return False

    # Only allow safe characters
    # Alphanumeric, spaces, hyphens, underscores, dots
    pattern = r'^[\w\s\.-]+$'
    if not re.match(pattern, filename):
        return False

    # Don't allow hidden files (start with dot)
    if filename.startswith('.'):
        return False

    # Don't allow dangerous Windows filenames
    windows_reserved = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    base_name = filename.split('.')[0].upper()
    if base_name in windows_reserved:
        return False

    return True


def safe_read_file(base_dir: str, filename: str, max_size: int = 10_000_000) -> str:
    """
    Safely read file with path traversal protection and size limits.

    Args:
        base_dir: Base directory for file
        filename: Filename (must pass safe_filename check)
        max_size: Maximum file size in bytes (default: 10MB)

    Returns:
        File contents

    Raises:
        PathTraversalError: If filename tries to escape base_dir
        ValueError: If filename is invalid
        OSError: If file too large or read fails
    """
    if not safe_filename(filename):
        raise ValueError(f"Invalid filename: {filename}")

    filepath = safe_path_join(base_dir, filename)

    # Check file size before reading
    file_size = os.path.getsize(filepath)
    if file_size > max_size:
        raise OSError(f"File too large: {file_size} bytes (max: {max_size})")

    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def safe_write_file(base_dir: str, filename: str, content: str) -> None:
    """
    Safely write file with atomic operation and path traversal protection.

    Args:
        base_dir: Base directory for file
        filename: Filename (must pass safe_filename check)
        content: Content to write

    Raises:
        PathTraversalError: If filename tries to escape base_dir
        ValueError: If filename is invalid
    """
    if not safe_filename(filename):
        raise ValueError(f"Invalid filename: {filename}")

    filepath = safe_path_join(base_dir, filename)

    # Write to temporary file first (atomic operation)
    temp_file = filepath + '.tmp'

    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # Atomic rename
        shutil.move(temp_file, filepath)

    except Exception as e:
        # Cleanup temp file on error
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        raise


def safe_read_json(base_dir: str, filename: str, max_size: int = 10_000_000) -> dict:
    """
    Safely read JSON file with path traversal protection.

    Args:
        base_dir: Base directory for file
        filename: Filename (must pass safe_filename check)
        max_size: Maximum file size in bytes (default: 10MB)

    Returns:
        Parsed JSON dictionary

    Raises:
        PathTraversalError: If filename tries to escape base_dir
        ValueError: If filename is invalid or JSON is malformed
        OSError: If file too large or read fails
    """
    import json

    content = safe_read_file(base_dir, filename, max_size)
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filename}: {e}")


def safe_write_json(base_dir: str, filename: str, data: dict) -> None:
    """
    Safely write JSON file with atomic operation and path traversal protection.

    Args:
        base_dir: Base directory for file
        filename: Filename (must pass safe_filename check)
        data: Dictionary to write as JSON

    Raises:
        PathTraversalError: If filename tries to escape base_dir
        ValueError: If filename is invalid or data is not JSON-serializable
    """
    import json

    try:
        content = json.dumps(data, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Failed to serialize data to JSON: {e}")

    safe_write_file(base_dir, filename, content)


if __name__ == "__main__":
    # Test safe path operations
    import pytest

    # Test path traversal prevention
    try:
        safe_path_join('/app/data', '../../../etc/passwd')
        print("❌ FAIL: Path traversal not detected")
    except PathTraversalError:
        print("✅ PASS: Path traversal detected")

    # Test safe filename validation
    assert safe_filename('file.txt') == True
    assert safe_filename('../../../etc/passwd') == False
    assert safe_filename('file<script>.txt') == False
    print("✅ PASS: Filename validation")

    print("✅ All security tests passed")
