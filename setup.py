"""
Setup script for CPG Compliance AI Agents
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def setup_environment():
    """Setup the development environment."""
    print("🚀 Setting up CPG Compliance AI Agents environment...\n")
  
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        return False
  
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
  
    # Create virtual environment
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
  
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
  
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        return False
  
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing Python dependencies"):
        return False
  
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path(".env.example")
        if env_example.exists():
            env_file.write_text(env_example.read_text())
            print("✅ Created .env file from .env.example")
        else:
            print("⚠️  .env.example not found, please create .env manually")
  
    # Create data directories
    data_dirs = [
        "data/contracts",
        "data/planograms", 
        "data/images",
        "data/reports",
        "data/cache",
        "data/memory",
        "logs"
    ]
  
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
  
    print("✅ Created data directories")
  
    # Setup dashboard (if Node.js is available)
    if subprocess.run("node --version", shell=True, capture_output=True).returncode == 0:
        dashboard_dir = Path("dashboard")
        if dashboard_dir.exists():
            os.chdir(dashboard_dir)
            if run_command("npm install", "Installing dashboard dependencies"):
                os.chdir("..")
                print("✅ Dashboard setup completed")
            else:
                os.chdir("..")
                print("⚠️  Dashboard setup failed")
        else:
            print("⚠️  Dashboard directory not found")
    else:
        print("⚠️  Node.js not found, skipping dashboard setup")
  
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Configure .env file with your settings")
    print("3. Run the application: python main.py")
    print("4. Or use CLI: python cli.py --help")
  
    return True

if __name__ == "__main__":
    setup_environment()