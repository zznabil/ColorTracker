# PROJECT KNOWLEDGE BASE (TESTS)

**Directory:** `tests/`
**Scope:** Verification, Performance Auditing, and Robustness Suite.

## OVERVIEW

The testing layer ensures surgical precision of **Sage (Logic)** while enforcing strict performance invariants. It focuses on three pillars:
1.  **Deterministic Logic**: Verifying vision algorithms and motion physics with zero hardware dependency.
2.  **Performance Auditing**: Automated regression testing for O(1) memory allocation and sub-millisecond throughput.
3.  **Chaos & Robustness**: Stress testing against "User From Hell" scenarios (rapid config changes) and malformed hardware inputs.

## WHERE TO LOOK

| Component | Location | Role |
|-----------|----------|------|
| **Fixtures** | `tests/conftest.py` | Global `MockScreenShot` factory and automatic WinAPI suppression for cross-platform runs. |
| **Chaos Monkey** | `tests/test_ultra_robustness.py` | Multi-threaded config fuzzing and marathon stability (100k+ frames). |
| **Perf Auditing** | `tests/test_low_level_movement_opt.py` | Asserts object identity for structure reuse (zero-allocation verification). |
| **Loop Throughput** | `tests/test_integration_stress.py` | End-to-end pipeline latency auditing (<10ms target). |
| **Vision Mocking** | `tests/test_detection_mocked.py` | Verification of target acquisition using static memory buffers and `numpy` views. |
| **Math Validation** | `tests/test_movement_math.py` | Floating-point precision and coordinate scaling (0-65535) verification. |

## CONVENTIONS

- **Mock Hardware Strategy**: 
  - **Vision**: Use `MockScreenShot` with pre-allocated `numpy` arrays. Never invoke `mss` real screen capture in unit tests.
  - **Input**: Always patch `ctypes.windll.user32.SendInput`. Use `mock_windows_api` fixture.
  - **Absolute Identity Asserts**: 
    - For performance optimizations (e.g., structure reuse), use `assert obj1 is obj2`. 
    - This verifies that Sage is reusing memory rather than triggering GC.
  - **Deterministic Time**: Patch `time.time` and `time.perf_counter` in motion engine tests to simulate perfectly stable framerates.
  - **Duality Testing**: 
    - **Vertical Deep Coverage**: Focus on edge-case logic (e.g., target at ROI boundary, zero-length movement).
    - **Horizontal Broad Coverage**: Focus on parameter ranges and component interactions.
  - **Non-Deterministic Mocks**: Mocks must return consistent data to ensure vision logic tests are repeatable.
  - **Implicit Allocation**: Avoid tests that pass but ignore new object creation in hot paths; always prefer identity checks for optimized classes.
  - **Real WinAPI Calls**: Strictly forbidden in unit/logic tests. Tests must be runnable on non-Windows platforms.
  - **Real Screen Capture**: Forbidden. Prevents test flakiness and dependency on desktop state/resolution.
  - **Time/Sleep Dependence**: Avoid `time.sleep()`. Use patched time or counters for deterministic "marathon" simulations.
  - **Non-Deterministic Mocks**: Mocks must return consistent data to ensure vision logic tests are repeatable.

## COMMANDS

```bash
# Run full suite
python -m pytest

# Run performance regression tests (O(1) checks)
python -m pytest tests/test_low_level_movement_opt.py -v

# Run stability marathon (Stress test)
python -m pytest tests/test_ultra_robustness.py -v
```

## V3.4.1 TEST COVERAGE

- **Total Tests**: 128
- **Status**: ✅ 100% PASSING (128/128 tests)
- **New Tests (V3.4.1)**:
  - `test_get_stats_comprehensive`: Validates 1% Low FPS calculation with sufficient data.
  - `TestProbeEmptyHistory`: Covers edge cases for telemetry probes with no data or incomplete recordings.
  - **Passing Rate**: 100% (18/18 tests passing) for `test_performance_monitor.py`.
- **Updated Tests**: Fixed `test_horizontal_broad_coverage.py` to align with Stealth Protocol (exclusive use of absolute coordinates 0-65535).
- **Coverage**:
  - Unit tests for all core modules
  - Integration tests for full pipeline
  - Edge case scenarios (ultra-robustness)
  - Performance regression tests
  - Memory identity verification tests
  - Thread safety and concurrency tests
  - Configuration boundary and validation tests
