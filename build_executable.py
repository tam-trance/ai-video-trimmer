"""
Build script for creating the VideoProcessor executable
"""

import os
import platform
import shutil
import subprocess
import sys


def run_command(command):
    """Run a command and print its output"""
    print(f"\nRunning: {' '.join(command)}")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True,
    )

    for line in process.stdout:
        print(line, end="")

    process.wait()
    return process.returncode


def build_executable():
    """Build the executable using PyInstaller"""
    print("=== Video Processor Executable Builder ===")

    # Create resources first
    print("\nStep 1: Creating resources...")
    try:
        if not os.path.exists("splash.png") or not os.path.exists("icon.ico"):
            if run_command([sys.executable, "create_resources.py"]) != 0:
                print("Warning: Failed to create resources. Continuing anyway.")
    except Exception as e:
        print(f"Warning: Failed to create resources: {e}. Continuing anyway.")

    # Clean up previous builds - be more thorough
    print("\nStep 2: Cleaning up previous builds...")
    for directory in ["build", "dist", "VideoProcessor-Dist", "__pycache__"]:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"Removed {directory} directory")
            except Exception as e:
                print(f"Warning: Failed to remove {directory}: {e}")

    # Also remove spec files
    for spec_file in ["VideoProcessor.spec", "VideoProcessor-Simple.spec"]:
        if os.path.exists(spec_file):
            try:
                os.remove(spec_file)
                print(f"Removed {spec_file}")
            except Exception as e:
                print(f"Warning: Failed to remove {spec_file}: {e}")

    # Install PyInstaller and required dependencies
    print("\nStep 3: Ensuring required packages are installed...")
    try:
        import PyInstaller

        print("PyInstaller is already installed")
    except ImportError:
        print("Installing PyInstaller...")
        if run_command([sys.executable, "-m", "pip", "install", "pyinstaller"]) != 0:
            print("Error: Failed to install PyInstaller. Aborting.")
            return False

    # Install webrtcvad if it's not installed
    try:
        import webrtcvad

        print("webrtcvad is already installed")
    except ImportError:
        print("Installing webrtcvad...")
        if run_command([sys.executable, "-m", "pip", "install", "webrtcvad"]) != 0:
            print(
                "Warning: Failed to install webrtcvad. The executable may not work correctly."
            )

    # Install pydantic if not already installed
    try:
        import pydantic

        print("pydantic is already installed")
    except ImportError:
        print("Installing pydantic...")
        if run_command([sys.executable, "-m", "pip", "install", "pydantic"]) != 0:
            print(
                "Warning: Failed to install pydantic. The executable may not work correctly."
            )

    # Make sure main.py contents are properly accessible
    print("\nStep 4: Validating imports...")
    try:
        # Test the imports that will be needed
        with open("app.py", "r") as f:
            print("app.py exists and is readable")
    except Exception as e:
        print(f"Warning: Couldn't read app.py: {e}")

    # Create necessary folders that will be bundled with the executable
    print("\nStep 5: Creating necessary folders...")
    for folder in ["raw", "audio", "jsons", "edited", "subtitles", "logs"]:
        os.makedirs(folder, exist_ok=True)
        print(f"Created {folder} directory")

    # Build the GUI application - use onefile mode for a single executable
    print("\nStep 6: Building the VideoProcessor application...")
    build_command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=VideoProcessor",
        "--onefile",  # Create a single executable file
        "--windowed",  # Hide the console window
        "--log-level=INFO",
        # Add required data files
        "--add-data",
        ".env;.",  # Include .env file with the executable
        # Add folder structures to the executable
        "--add-data",
        "raw;raw",
        "--add-data",
        "audio;audio",
        "--add-data",
        "jsons;jsons",
        "--add-data",
        "edited;edited",
        "--add-data",
        "subtitles;subtitles",
        "--add-data",
        "logs;logs",
        # Add hidden imports
        "--hidden-import=webrtcvad",
        "--hidden-import=pydub",
        "--hidden-import=src.audio.processing",
        "--hidden-import=src.llm.suggestion",
        "--hidden-import=src.transcription.whisper",
        "--hidden-import=src.utils.json_utils",
        "--hidden-import=src.utils.srt_utils",
        "--hidden-import=src.video.editor",
        # Add pydantic and its submodules to fix the missing module error
        "--hidden-import=pydantic",
        "--hidden-import=pydantic.deprecated",
        "--hidden-import=pydantic.deprecated.decorator",
        "--hidden-import=pydantic.json",
        "--hidden-import=pydantic.typing",
        "--hidden-import=pydantic.version",
        "--hidden-import=pydantic.fields",
        "--hidden-import=pydantic.main",
        "--hidden-import=pydantic.config",
        "--hidden-import=pydantic.class_validators",
        "--hidden-import=pydantic.error_wrappers",
        "--hidden-import=pydantic.errors",
        "--hidden-import=pydantic.schema",
        "--hidden-import=pydantic.color",
        "--hidden-import=pydantic.networks",
        "--hidden-import=pydantic.datetime_parse",
        "--hidden-import=pydantic.types",
        # Also include langchain dependencies
        "--hidden-import=langchain",
        "--hidden-import=langchain_google_genai",
    ]

    if os.path.exists("icon.ico"):
        build_command.append("--icon=icon.ico")

    # Add app.py as the main file
    build_command.append("app.py")

    if run_command(build_command) != 0:
        print("Error: Failed to build the application. Aborting.")
        return False

    # Copy the executable to the root directory for easy access
    try:
        source_exe = os.path.join("dist", "VideoProcessor.exe")
        if os.path.exists(source_exe):
            shutil.copy(source_exe, "VideoProcessor.exe")
            print(f"Copied VideoProcessor.exe to root directory for easy access")
        else:
            print(f"Warning: Couldn't find {source_exe}")
    except Exception as e:
        print(f"Warning: Failed to copy executable: {e}")

    print("\n=== Build Complete ===")
    print("The application is located in the 'dist' folder")
    print("A copy has also been placed in the root directory for convenience")
    print("You can now run VideoProcessor.exe directly")
    return True


if __name__ == "__main__":
    build_executable()
    input("\nPress Enter to exit...")
