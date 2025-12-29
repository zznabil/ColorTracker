# Plan: Deep Stealth - Input Integrity

## Phase 1: Architecture Refactoring

- [x] Task: Refactor LowLevelMovementSystem to Engine Strategy [62ece0c]
    - [ ] Subtask: Create BaseEngine interface and StandardEngine implementation.
    - [ ] Subtask: Write unit tests verifying engine switching does not break coordinate clamping.
- [x] Task: Port Standard Logic to Engine A [62ece0c]
    - [ ] Subtask: Migrate existing SendInput logic into a concrete StandardEngine class.
    - [ ] Subtask: Verify all existing movement tests pass with the new architecture.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Architecture Refactoring' (Protocol in workflow.md)

## Phase 2: Stealth Engine Implementation

- [ ] Task: Implement Logitech Driver Proxy (Engine B)
    - [ ] Subtask: Research DLL entry points for lghub_agent.exe input simulation.
    - [ ] Subtask: Implement the LogitechEngine with environment auto-detection.
- [ ] Task: Implement Flag Masking Hook (Engine C)
    - [ ] Subtask: Implement WH_MOUSE_LL hook in Python ctypes.
    - [ ] Subtask: Verify flag clearing behavior using a diagnostic hook tool.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Stealth Engine Implementation' (Protocol in workflow.md)

## Phase 3: GUI & Integration

- [ ] Task: Update SYSTEM Tab UI
    - [ ] Subtask: Add the dropdown and link it to the movement engine factory.
- [ ] Task: Final Verification & Clean-up
    - [ ] Subtask: Ensure 100% test pass and Ruff compliance.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: GUI & Integration' (Protocol in workflow.md)
