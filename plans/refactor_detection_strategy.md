# Refactoring Plan: DetectionSystem Capture Strategy

## Objective
Replace direct `mss` usage in `core/detection.py` with a Strategy Pattern (`CaptureBackend`) to support future backends (e.g., DXGI) and allow runtime switching/rollback.

## Current State
- `DetectionSystem` manages `mss` instances using `threading.local()`.
- Capture logic is tightly coupled in `_capture_and_process_frame`.
- `np.frombuffer` optimization is specific to `mss` raw bytes.

## Proposed Architecture

### 1. Abstract Base Class (`CaptureBackend`)
Located in `core/capture.py` (new file).
```python
class CaptureBackend(ABC):
    @abstractmethod
    def grab(self, area: dict) -> NDArray[np.uint8]:
        """Returns image as BGRA numpy array"""
        pass
        
    @abstractmethod
    def close(self):
        pass
```

### 2. Concrete Implementations
- `MSSBackend`: Wraps existing `mss` logic. Needs to handle `threading.local` if the backend instance is shared, OR `DetectionSystem` maintains thread-local backends.
  - *Decision*: `DetectionSystem` will keep `threading.local` which holds the *backend instance*. The backend class itself can be lightweight.

### 3. DetectionSystem Updates
- Remove `import mss`.
- Add `capture_method` to Config (default "mss").
- In `_get_backend()` (renamed `_get_sct`):
  - Instantiate `MSSBackend` or `DXGIBackend` based on config.
  - Store in `self._local.backend`.

## Sequence of Changes

1.  **Create `core/capture.py`**:
    - Define `CaptureBackend` (ABC).
    - Implement `MSSBackend`.
2.  **Modify `Config` (in `utils/config.py`)**:
    - Add `capture_method` (default "mss").
    - Add `capture_method` validation.
3.  **Refactor `core/detection.py`**:
    - Import `CaptureBackendFactory` (or simple logic).
    - Replace `_get_sct` with `_get_backend`.
    - Update `_capture_and_process_frame` to use `backend.grab(area)`.
4.  **Verify**:
    - Run `tests/test_detection_mocked.py`.

## Rollback Strategy (DXGI Failure)
- **Feature Flag**: `capture_method` in config.
- **Auto-Fallback**:
    ```python
    try:
        backend = DXGIBackend()
    except Exception:
        logger.error("DXGI init failed, falling back to MSS")
        backend = MSSBackend()
    ```
- This logic goes in the factory/instantiation method.

## Verification
- Run existing tests.
- Add new test `tests/test_capture_strategy.py` to verify backend switching.
