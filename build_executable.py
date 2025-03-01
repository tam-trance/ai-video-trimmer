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

    # Make sure main.py contents are properly accessible
    print("\nStep 4: Validating imports...")
    try:
        # Test the imports that will be needed
        with open("main.py", "r") as f:
            print("main.py exists and is readable")
    except Exception as e:
        print(f"Warning: Couldn't read main.py: {e}")

    # Build the GUI application - use onedir mode for faster loading
    print("\nStep 5: Building the VideoProcessor application...")
    build_command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=VideoProcessor",
        # Using onedir instead of onefile for faster loading
        "--log-level=INFO",
        "--add-data",
        ".env;.",  # Include .env file with the executable
        # Add hidden imports
        "--hidden-import=webrtcvad",
        "--hidden-import=pydub",
        "--hidden-import=src.audio.processing",
        "--hidden-import=src.llm.suggestion",
        "--hidden-import=src.transcription.whisper",
        "--hidden-import=src.utils.json_utils",
        "--hidden-import=src.utils.srt_utils",
        "--hidden-import=src.video.editor",
    ]

    if os.path.exists("icon.ico"):
        build_command.append("--icon=icon.ico")

    build_command.append("app.py")

    if run_command(build_command) != 0:
        print("Error: Failed to build the application. Aborting.")
        return False

    # Create a distribution folder
    print("\nStep 6: Creating a distribution package...")
    dist_folder = "VideoProcessor-Dist"

    try:
        # Create distribution folder
        if os.path.exists(dist_folder):
            shutil.rmtree(dist_folder)
        os.makedirs(dist_folder)

        # Copy the entire dist/VideoProcessor folder
        dist_path = os.path.join("dist", "VideoProcessor")
        if os.path.exists(dist_path):
            # Copy the entire VideoProcessor folder
            shutil.copytree(dist_path, os.path.join(dist_folder, "VideoProcessor"))
            print(f"Copied VideoProcessor folder to distribution folder")

            # Create a batch file to run the executable
            batch_path = os.path.join(dist_folder, "Run_VideoProcessor.bat")
            with open(batch_path, "w") as f:
                f.write("@echo off\n")
                f.write("cd VideoProcessor\n")
                f.write("start VideoProcessor.exe\n")
            print(f"Created batch file launcher")
        else:
            print(f"Warning: Couldn't find {dist_path}")

        # Create empty folders
        for folder in ["audio", "jsons", "edited", "subtitles", "logs"]:
            os.makedirs(
                os.path.join(dist_folder, "VideoProcessor", folder), exist_ok=True
            )
            print(f"Created {folder} directory in distribution")

        # Create .env file if it doesn't exist
        env_path = os.path.join(dist_folder, "VideoProcessor", ".env")
        if not os.path.exists(".env"):
            with open(env_path, "w") as f:
                f.write("# API Keys and Configuration\n")
                f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
            print("Created template .env file")
        else:
            shutil.copy(".env", env_path)
            print("Copied existing .env file")

        # Create README
        with open(os.path.join(dist_folder, "README.txt"), "w") as f:
            f.write("=== Video Processor ===\n\n")
            f.write("How to use:\n")
            f.write(
                "1. Edit the .env file in the VideoProcessor folder to add your API keys\n"
            )
            f.write("2. Double-click Run_VideoProcessor.bat to start the application\n")
            f.write("3. Click 'Browse' to select your video file\n")
            f.write("4. Choose your output options\n")
            f.write("5. Click 'Process Video'\n\n")
            f.write(
                "Output files will be placed in these folders inside the VideoProcessor directory:\n"
            )
            f.write("- subtitles: SRT subtitle files\n")
            f.write("- edited: Final edited videos\n")
            f.write("- jsons: Raw transcript data\n")
        print("Created README file")

    except Exception as e:
        print(f"Warning: Failed to create distribution package: {e}")

    print("\n=== Build Complete ===")
    print(f"The application is located in the '{dist_folder}' folder")
    print(f"Double-click Run_VideoProcessor.bat to start the application")
    return True


if __name__ == "__main__":
    build_executable()
    input("\nPress Enter to exit...")
