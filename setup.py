"""
Comprehensive setup script for video-editor-script
Handles all dependencies, ffmpeg setup, and can run the application
"""

import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

# List of all required Python packages
DEPENDENCIES = {
    # Core dependencies
    "setuptools": ">=65.5.1",  # For pkg_resources
    "python-dotenv": ">=1.0.0",
    "pydub": "==0.25.1",
    "webrtcvad": "==2.0.10",
    "numpy": ">=1.17.3",
    # OpenAI and LLM related
    "openai": ">=1.6.0",
    "langchain": ">=0.0.267",
    "langchain-core": ">=0.1.1",
    "langchain-community": ">=0.0.10",
    "langchain-google-genai": ">=0.0.3",
    "google-generativeai": ">=0.3.0",
    # HTTP libraries with correct versions
    "httpx": ">=0.23.0,<0.26.0",  # Compatible with gotrue
    # Video/audio processing
    "ffmpeg-python": ">=0.2.0",
    # MoviePy dependencies (installed separately to avoid conflicts)
    "decorator": ">=4.0.11",
    "imageio": ">=2.5.0",
    "imageio-ffmpeg": ">=0.4.2",
    "proglog": ">=0.1.9",
    "tqdm": ">=4.11.2",
    "python-dotenv": "==1.0.1",
    "moviepy": "==1.0.3",
}


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60 + "\n")


def install_dependencies(run_type="full"):
    """Install all required Python dependencies"""
    print_header("Installing Python Dependencies")

    # Check if in virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    if not in_venv:
        print("NOTE: You're not using a virtual environment.")
        print("It's recommended to use a virtual environment to avoid conflicts.")
        print("But we'll continue with the global Python installation...\n")

    # First uninstall potentially problematic packages to avoid conflicts
    if run_type == "full":
        for pkg in ["moviepy", "langchain"]:
            try:
                print(f"Removing {pkg} if installed...")
                subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y", pkg])
            except:
                pass

    # Install setuptools first (needed for pkg_resources)
    print("Installing setuptools...")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            f"setuptools{DEPENDENCIES['setuptools']}",
        ]
    )

    # Install dependencies in groups to minimize conflicts

    # 1. Basic utilities first
    print("\nInstalling core utilities...")
    for pkg in ["python-dotenv", "numpy", "tqdm", "decorator", "proglog"]:
        if pkg in DEPENDENCIES:
            spec = f"{pkg}{DEPENDENCIES[pkg]}"
            print(f"Installing {spec}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", spec])
            except Exception as e:
                print(f"Warning: Failed to install {spec}: {e}")

    # 2. Install audio libraries
    print("\nInstalling audio processing libraries...")
    for pkg in ["pydub", "webrtcvad", "ffmpeg-python"]:
        if pkg in DEPENDENCIES:
            spec = f"{pkg}{DEPENDENCIES[pkg]}"
            print(f"Installing {spec}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", spec])
            except Exception as e:
                print(f"Warning: Failed to install {spec}: {e}")

    # 3. Install HTTP libraries
    print("\nInstalling HTTP libraries...")
    for pkg in ["httpx"]:
        if pkg in DEPENDENCIES:
            spec = f"{pkg}{DEPENDENCIES[pkg]}"
            print(f"Installing {spec}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", spec])
            except Exception as e:
                print(f"Warning: Failed to install {spec}: {e}")

    # 4. Install image and video processing
    print("\nInstalling image and video processing...")
    for pkg in ["imageio", "imageio-ffmpeg"]:
        if pkg in DEPENDENCIES:
            spec = f"{pkg}{DEPENDENCIES[pkg]}"
            print(f"Installing {spec}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", spec])
            except Exception as e:
                print(f"Warning: Failed to install {spec}: {e}")

    # 5. Install moviepy separately because it's finicky
    print("\nInstalling moviepy...")
    try:
        spec = f"moviepy{DEPENDENCIES['moviepy']}"
        subprocess.check_call([sys.executable, "-m", "pip", "install", spec])
        print(f"Successfully installed {spec}")
    except Exception as e:
        print(f"Error installing moviepy: {e}")
        print("Trying alternative installation method...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--upgrade", "moviepy"]
            )
            print("Successfully installed moviepy (latest version)")
        except:
            print("Warning: MoviePy installation may have failed.")

    # 6. Install langchain and OpenAI
    print("\nInstalling LLM libraries...")
    for pkg in [
        "openai",
        "langchain",
        "langchain-core",
        "langchain-community",
        "langchain-google-genai",
        "google-generativeai",
    ]:
        if pkg in DEPENDENCIES:
            spec = f"{pkg}{DEPENDENCIES[pkg]}"
            print(f"Installing {spec}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", spec])
            except Exception as e:
                print(f"Warning: Failed to install {spec}: {e}")

    # Verify important packages
    print("\nVerifying installations...")
    packages_to_verify = [
        "openai",
        "langchain",
        "moviepy",
        "pydub",
        "webrtcvad",
        "google_generativeai",
        "langchain_google_genai",
    ]
    all_successful = True

    for pkg in packages_to_verify:
        try:
            cmd = [sys.executable, "-c", f"import {pkg}; print(f'{pkg} is installed')"]
            subprocess.check_call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"✓ {pkg} is installed correctly")
        except:
            print(f"✗ {pkg} installation may have failed")
            all_successful = False

    if all_successful:
        print("\nAll Python dependencies installed successfully!")
    else:
        print("\nSome dependencies may not have installed correctly.")
        print("You might still be able to run the script, but there could be issues.")

    return all_successful


def download_progress(block_num, block_size, total_size):
    """Show download progress"""
    downloaded = block_num * block_size
    percent = min(int(downloaded * 100 / total_size), 100)
    sys.stdout.write(f"\rDownloading: {percent}% [{downloaded} / {total_size}]")
    sys.stdout.flush()


def setup_ffmpeg():
    """Check for ffmpeg and install if needed"""
    print_header("Setting up FFmpeg")

    # First check if ffmpeg is already available
    ffmpeg_available = False
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            print("FFmpeg is already installed and accessible in PATH.")
            ffmpeg_available = True
    except:
        print("FFmpeg is not available in PATH.")

    if ffmpeg_available:
        # Set environment variables for the FFmpeg in PATH
        try:
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path:
                # Set environment variables for this session
                os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
                print(f"Using FFmpeg from: {ffmpeg_path}")

                # Add to .env file
                update_env_file("IMAGEIO_FFMPEG_EXE", ffmpeg_path)

                return True
        except Exception as e:
            print(f"Error setting up FFmpeg environment: {e}")

    # If we're here, FFmpeg is not in PATH or not correctly configured
    if platform.system().lower() == "windows":
        # Check if we already have ffmpeg in the bin directory
        bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
        ffmpeg_exe = os.path.join(bin_dir, "ffmpeg.exe")

        if os.path.exists(ffmpeg_exe):
            print(f"Found FFmpeg in local bin directory: {ffmpeg_exe}")
            setup_local_ffmpeg(bin_dir, ffmpeg_exe)
            return True

        # Ask the user if they want to download FFmpeg
        print("\nFFmpeg not found. It's required for audio/video processing.")
        choice = input("Download and install FFmpeg automatically? (y/n): ").lower()

        if choice == "y":
            # Download and install FFmpeg
            success = download_ffmpeg(bin_dir, ffmpeg_exe)
            if success:
                return True
        else:
            print("\nPlease install FFmpeg manually:")
            print("1. Download from: https://github.com/BtbN/FFmpeg-Builds/releases")
            print("2. Extract the zip file")
            print("3. Add the bin folder to your PATH environment variable")
            print("   or copy ffmpeg.exe to the 'bin' folder in this project")
            return False
    else:
        # For non-Windows systems, provide installation instructions
        print("FFmpeg is required but not found. Please install it:")
        if platform.system().lower() == "darwin":  # macOS
            print("For macOS, run: brew install ffmpeg")
        elif platform.system().lower() == "linux":
            print("For Ubuntu/Debian, run: sudo apt-get install ffmpeg")
            print("For CentOS/RHEL, run: sudo yum install ffmpeg")

        # Try using imageio-ffmpeg as a fallback
        print("\nAttempting to use imageio-ffmpeg as a fallback...")
        try:
            import imageio_ffmpeg

            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            if ffmpeg_path and os.path.exists(ffmpeg_path):
                print(f"Using FFmpeg from imageio_ffmpeg: {ffmpeg_path}")
                os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
                update_env_file("IMAGEIO_FFMPEG_EXE", ffmpeg_path)
                return True
            else:
                print("imageio_ffmpeg is installed but FFmpeg executable not found.")
        except Exception as e:
            print(f"Error using imageio_ffmpeg: {e}")

        return False


def download_ffmpeg(bin_dir, ffmpeg_exe):
    """Download FFmpeg for Windows"""
    try:
        # Create bin directory if it doesn't exist
        os.makedirs(bin_dir, exist_ok=True)

        # Download FFmpeg
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "ffmpeg.zip"
        )

        print(f"\nDownloading FFmpeg from {ffmpeg_url}")
        print("This may take a few minutes...")
        urlretrieve(ffmpeg_url, zip_path, download_progress)
        print("\nDownload complete!")

        # Extract the zip file
        print("Extracting FFmpeg...")
        temp_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "temp_ffmpeg"
        )
        os.makedirs(temp_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Find the ffmpeg.exe in the extracted folder
        for root, dirs, files in os.walk(temp_dir):
            if "ffmpeg.exe" in files:
                # Copy the files
                for exe in ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]:
                    src = os.path.join(root, exe)
                    dst = os.path.join(bin_dir, exe)
                    if os.path.exists(src):
                        shutil.copy(src, dst)
                        print(f"Copied {exe} to {dst}")
                break

        # Clean up
        os.remove(zip_path)
        shutil.rmtree(temp_dir)
        print("Temporary files cleaned up")

        # Verify FFmpeg was copied
        if not os.path.exists(ffmpeg_exe):
            print("Error: Failed to find ffmpeg.exe in the extracted files")
            return False

        # Set up the local FFmpeg
        setup_local_ffmpeg(bin_dir, ffmpeg_exe)
        return True

    except Exception as e:
        print(f"Error downloading FFmpeg: {e}")
        print("Please install FFmpeg manually")
        return False


def setup_local_ffmpeg(bin_dir, ffmpeg_exe):
    """Configure the system to use local FFmpeg"""
    bin_dir_abs = os.path.abspath(bin_dir)

    # Add to PATH for current session
    if bin_dir_abs not in os.environ["PATH"]:
        os.environ["PATH"] = bin_dir_abs + os.pathsep + os.environ["PATH"]
        print(f"Added {bin_dir_abs} to PATH for current session")

    # Set environment variables for moviepy and other libraries
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe

    # Update .env file
    update_env_file("FFMPEG_BINARY", ffmpeg_exe)
    update_env_file("IMAGEIO_FFMPEG_EXE", ffmpeg_exe)

    # Test if FFmpeg works now
    try:
        result = subprocess.run(
            [ffmpeg_exe, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            print("FFmpeg is working correctly!")
            return True
        else:
            print(f"Warning: FFmpeg at {ffmpeg_exe} may not be working correctly")
            return False
    except Exception as e:
        print(f"Error testing FFmpeg: {e}")
        return False


def update_env_file(key, value):
    """Update a key in the .env file"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

    # Create .env file if it doesn't exist
    if not os.path.exists(env_path):
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# Environment variables for video-editor-script\n")

    # Read existing content
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Check if key already exists
    key_exists = False
    new_lines = []

    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value.replace('\\', '/')}\n")
            key_exists = True
        else:
            new_lines.append(line)

    # Add key if it doesn't exist
    if not key_exists:
        new_lines.append(
            f"\n# FFmpeg configuration\n{key}={value.replace('\\', '/')}\n"
        )

    # Write back to file
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"Updated {key} in .env file")


def check_src_directory():
    """Make sure the src directory structure is correct"""
    print_header("Checking Source Directory Structure")

    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    if not os.path.exists(src_dir):
        print("Error: src directory not found!")
        return False

    # Check subdirectories
    required_dirs = ["audio", "llm", "transcription", "utils", "video"]
    for dir_name in required_dirs:
        dir_path = os.path.join(src_dir, dir_name)
        if not os.path.exists(dir_path):
            print(f"Error: {dir_name} directory not found in src!")
            return False

        # Create __init__.py if it doesn't exist
        init_file = os.path.join(dir_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                f.write("# Auto-generated __init__.py file\n")
            print(f"Created missing __init__.py in {dir_name}")

    # Make sure there's an __init__.py in src directory
    init_file = os.path.join(src_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w", encoding="utf-8") as f:
            f.write("# Auto-generated __init__.py file\n")
        print("Created missing __init__.py in src")

    print("Source directory structure looks good!")
    return True


def run_main_script():
    """Run the main.py script"""
    print_header("Running Main Script")

    main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    if not os.path.exists(main_path):
        print("Error: main.py not found!")
        return False

    print("Starting main.py...")
    print("-" * 60)

    # Run the main script
    result = subprocess.call([sys.executable, main_path])

    print("-" * 60)
    if result == 0:
        print("Script completed successfully!")
        return True
    else:
        print(f"Script exited with code {result}")
        return False


def main():
    """Main setup function"""
    print_header("Video Editor Script Setup")
    print("This script will set up all dependencies needed to run the video editor.")

    # Process arguments
    run_mode = "full"  # Default to full installation
    run_main = False  # Don't run main.py by default

    if len(sys.argv) > 1:
        if "quick" in sys.argv:
            run_mode = "quick"
            print("Running in quick mode (minimal setup)")
        if "run" in sys.argv:
            run_main = True
            print("Will run main.py after setup")

    # Install dependencies
    if not install_dependencies(run_mode):
        print("Warning: Some dependencies may not have installed correctly.")
        choice = input("Continue with setup anyway? (y/n): ")
        if choice.lower() != "y":
            print("Setup aborted.")
            return

    # Set up FFmpeg
    if not setup_ffmpeg():
        print("Warning: FFmpeg setup may not be complete.")
        choice = input("Continue anyway? (y/n): ")
        if choice.lower() != "y":
            print("Setup aborted.")
            return

    # Check source directory structure
    if not check_src_directory():
        print("Warning: Source directory structure may have issues.")
        choice = input("Continue anyway? (y/n): ")
        if choice.lower() != "y":
            print("Setup aborted.")
            return

    print_header("Setup Complete")
    print("All dependencies have been installed and configured.")

    # Run main.py if requested
    if run_main or input("Run main.py now? (y/n): ").lower() == "y":
        run_main_script()
    else:
        print("\nYou can now run the script with: python main.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup aborted by user.")
    except Exception as e:
        print(f"\nError during setup: {e}")
        import traceback

        traceback.print_exc()

    input("\nPress Enter to exit...")
