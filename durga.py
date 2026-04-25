import os
import sys
import subprocess

def run_server():
    print("Starting Django development server...")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Optional: Clear pycache to ensure fresh start
    print("Clearing pycache...")
    subprocess.run(["find", ".", "-name", "*.pyc", "-delete"], check=False)
    subprocess.run(["find", ".", "-name", "__pycache__", "-type", "d", "-exec", "rm", "-rf", "{}", "+"], check=False)

    execute_from_command_line(["manage.py", "runserver", "8000"])

if __name__ == '__main__':
    run_server()
