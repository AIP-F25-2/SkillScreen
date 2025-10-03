import subprocess
import os
import sys

def setup_skillscreen():
    """Setup SkillScreen with configuration and dependencies"""
    skillscreen_dir = os.path.join(os.path.dirname(__file__), 'SkillScreen')
    app_path = os.path.join(skillscreen_dir, 'app.py')
    requirements_path = os.path.join(skillscreen_dir, 'requirements.txt')
    setup_script = os.path.join(skillscreen_dir, 'setup_config.py')

    if not os.path.exists(skillscreen_dir):
        print(f"Error: SkillScreen directory not found at {skillscreen_dir}")
        return False
    if not os.path.exists(app_path):
        print(f"Error: app.py not found in SkillScreen directory at {app_path}")
        return False

    print("SkillScreen Setup & Launch")
    print("=" * 40)
    
    # Install dependencies
    print(f"Installing dependencies from {requirements_path}...")
    try:
        # Try to install full requirements first
        subprocess.run(['pip', 'install', '-r', requirements_path], check=True, cwd=skillscreen_dir)
        print("SUCCESS: Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Full dependencies failed to install: {e}")
        print("Installing minimal dependencies for dynamic app...")
        try:
            # Install minimal dependencies for dynamic app
            minimal_packages = [
                'streamlit==1.28.1',
                'google-generativeai==0.3.2',
                'python-docx==0.8.11',
                'PyPDF2==3.0.1',
                'requests==2.31.0',
                'python-dotenv==1.0.0'
            ]
            for package in minimal_packages:
                subprocess.run(['pip', 'install', package], check=True, cwd=skillscreen_dir)
            print("SUCCESS: Minimal dependencies installed successfully.")
        except subprocess.CalledProcessError as e2:
            print(f"ERROR: Failed to install even minimal dependencies: {e2}")
            return False

    # Setup configuration
    if os.path.exists(setup_script):
        print("Setting up configuration...")
        try:
            subprocess.run([sys.executable, setup_script], cwd=skillscreen_dir)
            print("SUCCESS: Configuration setup completed.")
        except Exception as e:
            print(f"WARNING: Configuration setup failed: {e}")
    else:
        print("WARNING: Setup script not found, skipping configuration setup")

    return True

def run_streamlit_app():
    """Run the Streamlit application"""
    skillscreen_dir = os.path.join(os.path.dirname(__file__), 'SkillScreen')
    
    # Try dynamic app first, then fallback to full app
    dynamic_app_path = os.path.join(skillscreen_dir, 'app_dynamic.py')
    app_path = os.path.join(skillscreen_dir, 'app.py')
    
    app_to_run = dynamic_app_path if os.path.exists(dynamic_app_path) else app_path
    
    print(f"Launching SkillScreen app from {app_to_run}...")
    try:
        subprocess.run(['streamlit', 'run', app_to_run], cwd=skillscreen_dir)
    except FileNotFoundError:
        print("ERROR: 'streamlit' command not found. Please ensure Streamlit is installed.")
        print("You can install it using: pip install streamlit")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        # Only run setup
        if setup_skillscreen():
            print("SUCCESS: Setup completed successfully!")
        else:
            print("ERROR: Setup failed!")
    else:
        # Run setup and launch
        if setup_skillscreen():
            run_streamlit_app()
        else:
            print("ERROR: Failed to setup SkillScreen")

if __name__ == "__main__":
    main()