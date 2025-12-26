@echo off
echo Building ColorTracker...
python -m PyInstaller --clean --noconfirm --onefile --windowed --name "ColorTracker" ^
    --hidden-import interception ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    --collect-all interception ^
    main.py
echo Copying config.json...
copy config.json dist\config.json
echo Build complete. Check dist/ folder.
pause
