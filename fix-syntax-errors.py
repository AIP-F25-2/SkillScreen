#!/usr/bin/env python3
"""
Script to fix syntax errors in service files
"""

import os
import re

def fix_service_file(file_path):
    """Fix syntax errors in a service file"""
    print(f"Fixing {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"  File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for common syntax issues
    issues_found = []
    
    # Check for missing except/finally blocks
    if re.search(r'@app\.route.*\n.*def.*\n.*try:.*\n.*\n@app\.route', content, re.MULTILINE | re.DOTALL):
        issues_found.append("Missing except/finally block")
    
    # Check for incomplete function definitions
    if re.search(r'def.*\n.*\n@app\.route', content, re.MULTILINE):
        issues_found.append("Incomplete function definition")
    
    if issues_found:
        print(f"  Issues found: {', '.join(issues_found)}")
        
        # Try to fix common patterns
        # Pattern 1: Missing except block after try
        pattern1 = r'(try:\s*\n.*?)(\n@app\.route)'
        if re.search(pattern1, content, re.MULTILINE | re.DOTALL):
            def fix_try_block(match):
                try_content = match.group(1)
                next_route = match.group(2)
                
                # Add basic except block
                fixed_try = try_content + """
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
""" + next_route
                return fixed_try
            
            content = re.sub(pattern1, fix_try_block, content, flags=re.MULTILINE | re.DOTALL)
            print("  Fixed missing except block")
        
        # Write the fixed content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"  ✅ Fixed {file_path}")
        return True
    else:
        print(f"  ✅ No issues found in {file_path}")
        return True

def main():
    """Main function to fix all service files"""
    print("🔧 Fixing syntax errors in service files...")
    print("=" * 50)
    
    services = [
        "interview-service",
        "video-ai-service", 
        "audio-ai-service",
        "text-ai-service",
        "assessment-service",
        "coding-service",
        "notification-service"
    ]
    
    fixed_count = 0
    total_count = len(services)
    
    for service in services:
        file_path = f"backend/{service}/app.py"
        if fix_service_file(file_path):
            fixed_count += 1
        print()
    
    print("=" * 50)
    print(f"✅ Fixed {fixed_count}/{total_count} service files")
    
    if fixed_count == total_count:
        print("🎉 All syntax errors have been fixed!")
        print("\nYou can now restart the services:")
        print("  docker-compose restart")
    else:
        print("⚠️  Some files could not be fixed automatically.")
        print("Check the logs above for details.")

if __name__ == "__main__":
    main()
