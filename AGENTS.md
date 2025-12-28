# AGENTS.md - ColorTracker Codebase Guide

## Quick Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Lint (Ruff)
python -m ruff check .

# Type check (Pyright)
python -m pyright .

# Run all tests
python -m pytest

# Run single test file
python -m pytest tests/test_detection_mocked.py

# Run single test function
python -m pytest tests/test_detection_mocked.py::test_find_target_success -v

# Run application
python main.py
```

## Code Style Guidelines

### Python & Types
- **Version**: Python 3.11+ with type hints required
- **Line length**: 120 characters (enforced by Ruff)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings

### Imports
```python
# Order: stdlib → third-party → local
import ctypes
from typing import Any
import numpy as np
from core.detection import DetectionSystem
```
- Combine-as-imports: true
- No wildcard imports

### Naming
- **Classes**: `PascalCase` (e.g., `DetectionSystem`, `MotionEngine`)
- **Functions/Methods**: `snake_case` (e.g., `find_target`, `process_motion`)
- **Variables**: `snake_case` (e.g., `target_x`, `frame_interval`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_FPS`)
- **Private members**: `_private_method`, `_private_var`

### Type Hints
```python
# ✅ Required for all public APIs
def process_motion(x: int, y: int, dt: float) -> tuple[int, int]:
    pass

class Config:
    screen_width: int
    target_fps: int
```

### Performance Optimizations
- Use `__slots__` for classes to reduce memory
- Cache local references in hot loops
- Use `np.frombuffer` for zero-copy operations
- Reuse ctypes structures to avoid allocation

```python
class MotionEngine:
    __slots__ = ('x_filter', 'y_filter', '_min_cutoff')

def algo_loop(self):
    find_target = self.detection.find_target
    while running:
        target = find_target()
```

### Error Handling
```python
# ✅ Specific exceptions with graceful fallbacks
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass  # Optional feature

# ✅ Validate and repair config values
def validate_value(key, value, schema):
    if not isinstance(value, schema["type"]):
        return schema["default"]
    return max(schema["min"], min(schema["max"], value))
```

### Documentation
- Module docstrings: `"""Detection System Module"""`
- Function docstrings: Return type and parameter descriptions
- Inline comments for complex math/logic

### Testing
- Framework: pytest
- Use fixtures for setup/teardown
- Mock Windows API for cross-platform testing
- Test naming: `test_[what]_[expected_behavior]`

```python
@pytest.fixture
def mock_detection():
    config = Config()
    return DetectionSystem(config)

def test_find_target_success(mock_detection):
    assert found == True
```

### Architectural Patterns

**Archetype A: The Sage (Logic/Data)** - `core/`, `utils/`
- Type-safety, O(1) memory, deterministic execution
- Examples: `DetectionSystem`, `MotionEngine`, `Config`

**Archetype B: The Artisan (Visual/Physics)** - `gui/`
- Aesthetics, HCI, motion physics
- Examples: `main_window.py`

### Safety & Validation
- Clamp coordinates to screen boundaries (0-65535)
- Validate all config values against min/max ranges
- Auto-repair corrupted config on load
- Emergency hotkeys (PageUp/PageDown)

### Configuration Schema
```python
DEFAULT_CONFIG = {
    "target_fps": {"type": int, "default": 240, "min": 30, "max": 1000},
    "fov_x": {"type": int, "default": 50, "min": 5, "max": 500},
    "motion_min_cutoff": {"type": float, "default": 0.5, "min": 0.01, "max": 25.0},
}
```

### Common Patterns
```python
# Config loading
config = Config()
config.load()  # Self-healing

# Performance monitoring
perf_monitor = PerformanceMonitor()
perf_monitor.record_frame(frame_time)
stats = perf_monitor.get_stats()

# Logging
logger = Logger(log_level=logging.DEBUG, log_to_file=True)
logger.info("Operation completed")

# Keyboard listener
keyboard = KeyboardListener(config)
keyboard.register_callback("page_up", start_callback)
keyboard.start()
```

### Project Structure
```
core/          # Detection, motion engine, low-level movement
gui/           # DearPyGui interface
utils/         # Config, logger, performance monitor, keyboard listener
tests/         # Pytest fixtures and test files
main.py        # Entry point
```

### Key Dependencies
- `dearpygui` - GUI framework
- `mss` - Screen capture
- `opencv-python` - Computer vision
- `numpy` - Numerical operations
- `pynput` - Keyboard listener

### Debugging
- Enable `debug_mode` in config for F12 debug console
- Use `logger.debug()` for verbose logging
- Check `PerformanceMonitor` stats for latency
- Run `pytest -v` for detailed test output
- Use `ruff check . --fix` for auto-fixing

---

**Version**: V3.2.3 | **Python**: 3.11+
