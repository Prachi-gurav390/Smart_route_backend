"""
Development environment setup script
"""
import subprocess
import sys
import os
import venv


def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True,
                                check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def setup_virtual_environment():
    """Set up Python virtual environment"""
    venv_path = "venv"

    if not os.path.exists(venv_path):
        print(f"🔄 Creating virtual environment at {venv_path}...")
        venv.create(venv_path, with_pip=True)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")

    # Determine activation script path based on OS
    if os.name == 'nt':  # Windows
        activate_script = os.path.join(venv_path, "Scripts", "activate")
        pip_path = os.path.join(venv_path, "Scripts", "pip")
    else:  # Unix/Linux/macOS
        activate_script = os.path.join(venv_path, "bin", "activate")
        pip_path = os.path.join(venv_path, "bin", "pip")

    # Install requirements
    if os.path.exists("requirements.txt"):
        if run_command(f"{pip_path} install -r requirements.txt", "Installing Python dependencies"):
            print("✅ Dependencies installed successfully")
        else:
            print("❌ Failed to install dependencies")
            return False

    return activate_script


def setup_mongodb():
    """Set up MongoDB for development"""
    print("\n🗃️  MongoDB Setup Options:")
    print("1. Use Docker (recommended)")
    print("2. Use local MongoDB installation")
    print("3. Skip MongoDB setup")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        if run_command("docker --version", "Checking Docker"):
            if run_command("docker run -d -p 27017:27017 --name smartroute_mongo mongo:7.0", "Starting MongoDB container"):
                print("✅ MongoDB container started on port 27017")
                return True
            else:
                print("⚠️  MongoDB container may already be running")
                return True
        else:
            print("❌ Docker not available")
            return False
    elif choice == "2":
        print("ℹ️  Please ensure MongoDB is installed and running on localhost:27017")
        return True
    else:
        print("⚠️  Skipping MongoDB setup")
        return True


def main():
    """Main development setup function"""
    print("🛠️  SmartRoute Development Setup")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    else:
        print(
            f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Set up virtual environment
    activate_script = setup_virtual_environment()
    if not activate_script:
        sys.exit(1)

    # Set up environment file
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            run_command("cp .env.example .env", "Creating environment file")
        else:
            print("⚠️  Creating basic .env file")
            with open(".env", "w") as f:
                f.write("MONGODB_URL=mongodb://localhost:27017\n")
                f.write("DATABASE_NAME=smartroute\n")

    # Set up MongoDB
    setup_mongodb()

    # Create data directories
    os.makedirs("data/gtfs", exist_ok=True)
    print("✅ Data directories created")

    # Success message
    print("\n" + "=" * 50)
    print("🎉 Development environment setup complete!")
    print("=" * 50)
    print("🐍 Activate virtual environment:")
    if os.name == 'nt':
        print(f"   {activate_script}")
    else:
        print(f"   source {activate_script}")
    print("\n🚀 Start the application:")
    print("   uvicorn app.main:app --reload")
    print("\n📊 Load sample data:")
    print("   python scripts/load_sample_data.py")
    print("\n🧪 Run tests:")
    print("   pytest tests/ -v")
    print("\n💡 API will be available at: http://localhost:8000")


if __name__ == "__main__":
    main()

