#!/usr/bin/env python3
"""Fix security imports to use deps module."""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix imports
    original_content = content
    
    # Fix get_current_user imports
    content = re.sub(
        r'from backend\.src\.core\.security import (.*)get_current_user(.*)',
        lambda m: f'from backend.src.api.deps import {m.group(1)}get_current_user{m.group(2)}',
        content
    )
    
    # Fix require_permissions imports
    content = re.sub(
        r'from backend\.src\.core\.security import (.*)require_permissions(.*)',
        lambda m: f'from backend.src.api.deps import {m.group(1)}PermissionChecker{m.group(2)}',
        content
    )
    
    # Only write if changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed imports in {file_path}")
        return True
    return False

def main():
    """Fix all imports in the backend directory."""
    backend_dir = Path("backend")
    fixed_count = 0
    
    # Process all Python files
    for py_file in backend_dir.rglob("*.py"):
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"\nFixed imports in {fixed_count} files")

if __name__ == "__main__":
    main()