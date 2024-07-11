import os
import subprocess

def generate_requirements(directory='.'):
    try:
        # Check if pipreqs is installed
        subprocess.check_call([os.sys.executable, '-m', 'pip', 'show', 'pipreqs'])
    except subprocess.CalledProcessError:
        print("pipreqs is not installed. Installing now...")
        subprocess.check_call([os.sys.executable, '-m', 'pip', 'install', 'pipreqs'])
    
    try:
        # Generate requirements.txt using pipreqs
        print(f"Generating requirements.txt in {directory}...")
        subprocess.check_call(['pipreqs', directory, '--force'])
        print("requirements.txt has been generated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate requirements.txt from the given directory.")
    parser.add_argument("directory", nargs='?', default='.', type=str, help="The directory to scan for requirements.")
    args = parser.parse_args()

    generate_requirements(args.directory)