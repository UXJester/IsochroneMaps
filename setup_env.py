import os
import subprocess
import shutil

# Define the virtual environment directory and requirements file
venv_dir = ".venv"
requirements_file = "requirements.txt"

# Step 1: Check if the virtual environment already exists or create it
if os.path.exists(venv_dir):
    print("Virtual environment already exists.")
    user_input = (
        input("Do you want to delete the existing environment and recreate it? (y/n): ")
        .strip()
        .lower()
    )
    if user_input == "y":
        print("Deleting existing virtual environment...")
        shutil.rmtree(venv_dir)
        print("Creating new virtual environment...")
        subprocess.run(["python3", "-m", "venv", venv_dir], check=True)
    else:
        print("Skipping virtual environment creation.")
else:
    print("Virtual environment not found. Creating virtual environment...")
    subprocess.run(["python3", "-m", "venv", venv_dir], check=True)

# Step 2: Activate the virtual environment and install requirements
activate_script = os.path.join(venv_dir, "bin", "activate")
install_command = f"source {activate_script} && pip install -r {requirements_file}"

# Check and prompt for pip upgrade
print("Checking pip version...")
check_pip_command = f"source {activate_script} && pip --version"
subprocess.run(check_pip_command, shell=True, executable="/bin/bash", check=True)

upgrade_pip_prompt = (
    input("Do you want to upgrade pip to the latest version? (y/n): ").strip().lower()
)
if upgrade_pip_prompt == "y":
    upgrade_pip_command = f"source {activate_script} && pip install --upgrade pip"
    subprocess.run(upgrade_pip_command, shell=True, executable="/bin/bash", check=True)

# Check if requirements file exists
if not os.path.exists(requirements_file):
    print(f"Requirements file '{requirements_file}' not found.")
    exit(1)

# Install requirements
print("Installing requirements...")
subprocess.run(install_command, shell=True, executable="/bin/bash", check=True)

print("Setup complete!")
