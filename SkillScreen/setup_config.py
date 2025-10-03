#!/usr/bin/env python3
"""
SkillScreen Configuration Setup Script
Helps users configure SkillScreen with proper settings
"""

import os
import json
from pathlib import Path
from config import config_manager, config

def setup_environment():
    """Setup environment variables and configuration"""
    print("SkillScreen Configuration Setup")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("Creating .env file from template...")
        try:
            with open("env.example", "r") as src:
                content = src.read()
            with open(".env", "w") as dst:
                dst.write(content)
            print("SUCCESS: .env file created successfully!")
        except Exception as e:
            print(f"ERROR: Error creating .env file: {e}")
            return False
    else:
        print("SUCCESS: .env file already exists")
    
    # Check if config.json exists
    config_file = Path("config.json")
    if not config_file.exists():
        print("Creating config.json file...")
        try:
            with open("config.json", "r") as f:
                config_data = json.load(f)
            print("SUCCESS: config.json file found!")
        except Exception as e:
            print(f"ERROR: Error reading config.json: {e}")
            return False
    else:
        print("SUCCESS: config.json file already exists")
    
    # Create logs directory
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("Creating logs directory...")
        logs_dir.mkdir(parents=True, exist_ok=True)
        print("SUCCESS: Logs directory created!")
    else:
        print("SUCCESS: Logs directory already exists")
    
    # Validate configuration
    print("\nValidating configuration...")
    if config_manager.validate_config():
        print("SUCCESS: Configuration is valid!")
    else:
        print("ERROR: Configuration has errors. Please check your settings.")
        return False
    
    # Check API key
    if not config.llm.api_key:
        print("\nWARNING: Gemini API key not set!")
        print("Please set GEMINI_API_KEY in your .env file")
        print("You can get your API key from: https://makersuite.google.com/app/apikey")
    else:
        print("SUCCESS: Gemini API key is configured")
    
    print("\nSetup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your Gemini API key")
    print("2. Run: streamlit run app.py")
    print("3. Start conducting interviews!")
    
    return True

def show_config():
    """Show current configuration"""
    print("Current Configuration")
    print("=" * 30)
    print(f"Debug Mode: {config.debug}")
    print(f"Environment: {config.environment}")
    print(f"Max Questions: {config.interview.max_questions}")
    print(f"Min Questions: {config.interview.min_questions}")
    print(f"LLM Model: {config.llm.model_name}")
    print(f"API Key Set: {'Yes' if config.llm.api_key else 'No'}")
    print(f"Log Level: {config.logging.level}")
    print(f"Log File: {config.logging.file_path}")

def main():
    """Main setup function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show_config()
    else:
        setup_environment()

if __name__ == "__main__":
    main()

