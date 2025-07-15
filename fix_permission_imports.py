#!/usr/bin/env python3
"""Fix permission imports to use PermissionChecker."""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix imports
    original_content = content
    
    # Replace require_permissions with PermissionChecker in import statements
    content = re.sub(
        r'from backend\.src\.api\.deps import (.*?)require_permissions(.*?)\n',
        r'from backend.src.api.deps import \1PermissionChecker\2\n',
        content
    )
    
    # Replace usage of require_permissions with PermissionChecker
    content = re.sub(
        r'\brequire_permissions\b',
        'PermissionChecker',
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
    
    # Process specific files that use require_permissions
    files_to_fix = [
        "backend/src/api/v1/workspaces.py",
        "backend/src/api/v1/organizations.py", 
        "backend/src/api/v1/agents.py",
        "backend/src/api/v1/prompts.py",
        "backend/src/api/v1/users.py"
    ]
    
    for file_path in files_to_fix:
        if Path(file_path).exists() and fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\nFixed imports in {fixed_count} files")

if __name__ == "__main__":
    main()