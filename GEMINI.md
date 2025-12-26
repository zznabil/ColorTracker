# ColorTracker

## Contents
- `core/`: core logic
- `gui/`: GUI
- `utils/`: utilities
- `tests/`: pytest suite
- `docs/`: manuals

## Runtime Dependencies
From `requirements.txt`:
- `dearpygui`
- `mss`
- `opencv-python`
- `numpy`
- `pyautogui`
- `pynput`

## Quality Gates
- `ruff check .`
- `pyright .`
- `python -m pytest`

## Verification
- Date: 2025-12-25
- `ruff`: All checks passed (0 errors)
- `pyright`: 0 errors, 0 warnings
- `pytest`: 134 passed (Python 3.12.8, pytest 7.4.0)
