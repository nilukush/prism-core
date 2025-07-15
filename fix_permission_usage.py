#!/usr/bin/env python3
"""Fix PermissionChecker usage to use it as a dependency."""

import os
import re
from pathlib import Path

def fix_usage_in_file(file_path):
    """Fix PermissionChecker usage in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix usage patterns
    original_content = content
    
    # Replace await PermissionChecker(current_user, [...]) with proper dependency usage
    # This is a bit complex - we need to modify the function signatures
    
    # For now, let's create a helper function approach
    if "await PermissionChecker(current_user," in content:
        # Add helper import if not present
        if "from backend.src.api.deps import" in content and "require_permissions" not in content:
            content = re.sub(
                r'(from backend\.src\.api\.deps import .*?)\n',
                r'\1\nfrom backend.src.api.deps import require_permissions\n',
                content,
                count=1
            )
        
        # Replace the usage pattern
        content = re.sub(
            r'await PermissionChecker\(current_user, \[(.*?)\]\)',
            r'require_permissions(current_user, [\1])',
            content
        )
    
    # Only write if changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed usage in {file_path}")
        return True
    return False

def main():
    """Fix all PermissionChecker usage."""
    files_to_fix = [
        "backend/src/api/v1/workspaces.py",
        "backend/src/api/v1/organizations.py", 
        "backend/src/api/v1/agents.py",
        "backend/src/api/v1/prompts.py",
        "backend/src/api/v1/users.py"
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        if Path(file_path).exists() and fix_usage_in_file(file_path):
            fixed_count += 1
    
    print(f"\nFixed usage in {fixed_count} files")

if __name__ == "__main__":
    main()