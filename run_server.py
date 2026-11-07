"""
Convenience launcher for Malawi Crop Intelligence Platform.
Starts the Django web backend & interactive dashboard on http://127.0.0.1:8000/
"""

import os
import sys
import subprocess
import webbrowser
import time

def main():
    print("=" * 75)
    print("  AGRIPRICE MALAWI - NATIONAL CROP INTELLIGENCE & ARBITRAGE SYSTEM")
    print("  Focus: Maize, Rice & Beans Across All 28 Districts of Malawi")
    print("=" * 75)
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(project_root, "backend")
    manage_py = os.path.join(backend_dir, "manage.py")
    
    if not os.path.exists(manage_py):
        print(f"Error: manage.py not found at {manage_py}")
        sys.exit(1)
        
    print("\nStarting Django REST Backend & Professional Web Dashboard...")
    print("Target URL: http://127.0.0.1:8000/\n")
    
    # Auto-open browser after 2 seconds
    def open_browser():
        time.sleep(2)
        print("Opening dashboard in web browser: http://127.0.0.1:8000/")
        webbrowser.open("http://127.0.0.1:8000/")
        
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Detect virtual environment python if not running inside it
    venv_python = os.path.join(project_root, ".venv", "Scripts", "python.exe")
    python_bin = sys.executable
    if os.path.exists(venv_python):
        python_bin = venv_python

    # Launch django runserver
    try:
        subprocess.run([python_bin, manage_py, "runserver", "0.0.0.0:8000"], cwd=backend_dir)
    except KeyboardInterrupt:
        print("\nServer stopped gracefully.")

if __name__ == "__main__":
    main()

