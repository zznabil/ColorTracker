LOGITECH STEALTH ENGINE - SETUP INSTRUCTIONS
==============================================

To enable the "Logitech Proxy (Experimental)" stealth engine, you need a specific DLL file.
This engine bypasses user-mode hooks by sending input directly through the Logitech driver.

OPTION 1: Manual DLL Placement (Recommended)
--------------------------------------------
1. Find a valid `logitech_g_hub.dll` or `ghub_device.dll`.
   - These can often be found in older "Logitech Gaming SDK" packages.
   - Or extracted from "Logitech Gaming Software 8.87".
   - Search GitHub for "logitech_g_hub.dll" or "ghub_device.dll".

2. Place the file in this folder:
   `C:\Users\Admin\Documents\ColorTracker\libs\ghub_device.dll`
   (Rename it if necessary)

OPTION 2: Install Legacy Software
---------------------------------
1. Download "Logitech Gaming Software 8.87.116" (64-bit).
   Link: https://download01.logi.com/web/ftp/pub/techsupport/gaming/LGS_8.87.116_x64_Logitech.exe

2. Install it. The ColorTracker will automatically find the SDK DLLs in:
   `C:\Program Files\Logitech Gaming Software\`

TROUBLESHOOTING
---------------
- If the engine fails to initialize, check the application logs.
- Ensure you are using the 64-bit DLL if running 64-bit Python.
