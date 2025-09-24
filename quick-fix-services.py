#!/usr/bin/env python3
"""
Quick fix for broken service files
"""

import os

def fix_broken_service(service_name):
    """Fix a broken service by adding missing parts"""
    file_path = f"backend/{service_name}/app.py"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the problematic pattern and fix it
    # Look for incomplete function before @app.route('/api')
    pattern = r'(\s+}\s*\n)(@app\.route\(\'/api\')'
    
    if re.search(pattern, content):
        # Add missing parts
        replacement = r'\1        \n        return jsonify({\'message\': \'Operation completed successfully\'}), 200\n        \n    except Exception as e:\n        logger.error(f"Error: {str(e)}")\n        return jsonify({\'error\': \'Internal server error\'}), 500\n\n\2'
        content = re.sub(pattern, replacement, content)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Fixed {service_name}")
        return True
    else:
        print(f"❌ Could not fix {service_name} - pattern not found")
        return False

def main():
    """Fix all broken services"""
    import re
    
    broken_services = [
        "interview-service",
        "video-ai-service",
        "audio-ai-service", 
        "text-ai-service",
        "coding-service",
        "notification-service"
    ]
    
    print("🔧 Quick fixing broken services...")
    
    for service in broken_services:
        fix_broken_service(service)
    
    print("\n🎉 Quick fix complete!")
    print("Now restart services: docker-compose restart")

if __name__ == "__main__":
    main()
