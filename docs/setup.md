# Setup & Deployment Guide: Zero to Hero

The `setup_and_run.ps1` script is the definitive orchestration path for installing and launching the Color Tracking Algo on fresh Windows environments.

## 🚀 The Clinical Path
1. **Prequisites**: Windows 10/11 version 22H2 or higher.
2. **Execution**:
   - Right-click `setup_and_run.ps1`.
   - Select **"Run with PowerShell"**.
   - If prompted for Administrator privileges, select **"Yes"**.

## 🛠 What the Script Does
- **Admin Elevation**: Ensures the script has rights to install Python and manage system paths.
- **Python Provisioning**: Checks for Python 3.12. If missing, it downloads and performs a silent installation of Python 3.12.
- **Venv Isolation**: Creates a local `.venv` to prevent dependency poisoning of the global system.
- **Requirement Sync**: Automatically installs all libraries in `requirements.txt`.
- **PyInstaller Compilation**: Uses the project's `.spec` file to build a fresh, high-performance `ColorTracker.exe`.
- **Seamless Launch**: Immediately starts the application upon successful build.

## ⚠️ Troubleshooting
- **Execution Policy**: If PowerShell blocks the script, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in a PowerShell terminal.
- **Path Conflicts**: If Python install fails, ensure no other Python 3.x installations are currently locking the `PATH` during setup.
- **Admin Rights**: The script **requires** elevation to handle the silent installer and environment variable refreshes.

## 🔄 Refreshing the Environment
To perform a "Force Reinstall", simply delete the `.venv/` and `dist/` folders and run the script again. It will rebuild everything from source with O(N) efficiency.

---
*Setup Guide Verified for V3.5.1 (Policeman & QoL Overhaul)*

