#!/usr/bin/env python3
"""
Setup Script for AI-Era Education Repository
Initialize environment and dependencies using uv
"""

import os
import sys
import subprocess
from pathlib import Path

# Global variable to store the uv command path
UV_COMMAND = "uv"


def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 9):
        print("Error: Python 3.9+ required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")


def check_uv_installation():
    """Check if uv is installed"""
    # Check common locations for uv
    uv_locations = [
        "uv",  # In PATH
        os.path.expanduser("~/.local/bin/uv"),  # User local installation
        os.path.expanduser("~/.cargo/bin/uv"),  # Cargo installation
    ]
    
    for uv_path in uv_locations:
        try:
            result = subprocess.run([uv_path, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ uv {result.stdout.strip()} detected at {uv_path}")
                # Set the global uv command for later use
                global UV_COMMAND
                UV_COMMAND = uv_path
                return True
        except (FileNotFoundError, PermissionError):
            continue
    
    print("✗ uv not found")
    return False


def install_uv():
    """Install uv if not present"""
    print("Installing uv...")
    try:
        # Try installing via pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"])
        print("✓ uv installed via pip")
        return True
    except subprocess.CalledProcessError:
        # Fallback to curl installation
        print("Attempting to install uv via curl...")
        try:
            subprocess.check_call([
                "curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"
            ], shell=True)
            print("✓ uv installed via curl")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install uv")
            print("Please install uv manually: https://docs.astral.sh/uv/getting-started/installation/")
            return False


def setup_virtual_environment():
    """Setup virtual environment using uv"""
    print("Setting up virtual environment with uv...")
    try:
        # Check if we're already in a virtual environment
        if os.getenv('VIRTUAL_ENV'):
            print("✓ Already in virtual environment")
            return True
        
        # Create virtual environment with uv
        subprocess.check_call([UV_COMMAND, "venv", ".venv"])
        print("✓ Virtual environment created at .venv/")
        
        # Provide activation instructions
        if os.name == 'nt':  # Windows
            activate_cmd = ".venv\\Scripts\\activate"
        else:  # Unix/Linux/macOS
            activate_cmd = "source .venv/bin/activate"
        
        print(f"💡 To activate virtual environment: {activate_cmd}")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to create virtual environment")
        return False


def install_dependencies():
    """Install dependencies using uv"""
    print("Installing dependencies with uv...")
    try:
        # Install main dependencies
        subprocess.check_call([UV_COMMAND, "sync"])
        print("✓ Dependencies installed successfully")
        
        # Install optional dev dependencies
        print("Installing development dependencies...")
        subprocess.check_call([UV_COMMAND, "sync", "--extra", "dev"])
        print("✓ Development dependencies installed")
        
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies")
        print("Falling back to pip installation...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
            print("✓ Dependencies installed via pip fallback")
            return True
        except subprocess.CalledProcessError:
            print("✗ Pip fallback also failed")
            return False


def setup_api_key():
    """Setup API key configuration"""
    print("\n🔑 API Key Configuration")
    
    # Check if API key already exists
    if os.getenv('GEMINI_API_KEY'):
        print("✓ GEMINI_API_KEY found in environment")
        return
    
    # Check .env file
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if 'GEMINI_API_KEY' in content:
                print("✓ Found GEMINI_API_KEY in .env file")
                return
    
    # Prompt for API key setup
    print("No Gemini API key found. Setting up...")
    print("\nYou can:")
    print("1. Get your API key from: https://aistudio.google.com/app/apikey")
    print("2. Set it as environment variable: export GEMINI_API_KEY='your-key'")
    print("3. Add it to .env file (recommended)")
    print("4. For custom endpoints, also set GEMINI_BASE_URL in .env")
    
    choice = input("\nWould you like to add API key to .env file now? (y/n): ").lower()
    
    if choice == 'y':
        api_key = input("Enter your Gemini API key: ").strip()
        if api_key:
            base_url = input("Enter Gemini base URL (press Enter for default): ").strip()
            
            # Save to .env file
            with open('.env', 'w') as f:
                f.write(f"GEMINI_API_KEY={api_key}\n")
                if base_url:
                    f.write(f"GEMINI_BASE_URL={base_url}\n")
                f.write(f"# CSV_FILE=data/your-papers.csv\n")
            print("✓ API key saved to .env file")
        else:
            print("✗ No API key provided")
    else:
        print("⚠️  Please set up API key manually before using the system")


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "data",
        "outputs",
        "tests"
    ]
    
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✓ Created: {dir_name}/")


def setup_git_hooks():
    """Setup git hooks for automatic README updates"""
    print("\n🔗 Setting up Git hooks...")
    
    if not Path('.git').exists():
        print("⚠️  Not a git repository, skipping git hooks")
        return
    
    # Create pre-commit hook
    hooks_dir = Path('.git/hooks')
    hooks_dir.mkdir(exist_ok=True)
    
    pre_commit_hook = hooks_dir / 'pre-commit'
    
    hook_content = '''#!/bin/bash
# Auto-update README before commit
if [ -f "data/classified_papers.json" ]; then
    uv run python scripts/update_readme.py update
    git add README.md
fi
'''
    
    with open(pre_commit_hook, 'w') as f:
        f.write(hook_content)
    
    # Make it executable
    pre_commit_hook.chmod(0o755)
    print("✓ Git pre-commit hook installed")


def create_uv_config():
    """Create uv configuration files"""
    print("\n⚙️  Setting up uv configuration...")
    
    # Create .python-version file for consistent Python version
    python_version_file = Path('.python-version')
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    with open(python_version_file, 'w') as f:
        f.write(f"{current_version}\n")
    print(f"✓ Created .python-version: {current_version}")
    
    # Create uv.lock if it doesn't exist (will be created by uv sync)
    print("✓ uv.lock will be created on first sync")


def print_usage():
    """Print usage instructions"""
    print("\n" + "="*60)
    print("🎓 AI-Era Education Repository Setup Complete!")
    print("="*60)
    
    print("\n📖 Quick Start with uv:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    
    print("\n2. Run commands using uv:")
    print("   uv run python scripts/classify_papers.py --csv data/your-papers.csv")
    print("   uv run python scripts/update_readme.py update")
    print("   uv run python scripts/incremental_update.py quick")
    
    print("\n3. Or use console scripts (after activation):")
    print("   classify-papers --csv data/your-papers.csv")
    print("   update-readme update")
    print("   incremental-update quick")
    
    print("\n4. Demo all features:")
    print("   uv run python demo.py")
    
    print("\n📚 For detailed usage, see: USAGE.md")
    
    print("\n🔧 uv Commands:")
    print("  - uv sync                  # Sync dependencies")
    print("  - uv add <package>         # Add new dependency")
    print("  - uv remove <package>      # Remove dependency")
    print("  - uv run <command>         # Run command in environment")
    print("  - uv shell                 # Activate shell in environment")
    
    print("\n🗂️  Configuration files:")
    print("  - pyproject.toml (dependencies)")
    print("  - .env (API keys)")
    print("  - .python-version (Python version)")
    print("  - uv.lock (locked dependencies)")


def main():
    """Main setup function"""
    print("🚀 Setting up AI-Era Education Repository with uv...")
    print("="*60)
    
    # Check prerequisites
    check_python_version()
    
    # Check and install uv
    if not check_uv_installation():
        if not install_uv():
            print("Setup failed: uv installation required")
            sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        print("Warning: Virtual environment setup failed, continuing...")
    
    # Install dependencies
    if not install_dependencies():
        print("Setup failed: Dependency installation required")
        sys.exit(1)
    
    # Setup API key
    setup_api_key()
    
    # Create directories
    create_directories()
    
    # Create uv configuration
    create_uv_config()
    
    # Setup git hooks
    setup_git_hooks()
    
    # Print usage instructions
    print_usage()
    
    print(f"\n🎉 Setup completed successfully!")
    print("Don't forget to activate your virtual environment before running commands.")


if __name__ == "__main__":
    main() 