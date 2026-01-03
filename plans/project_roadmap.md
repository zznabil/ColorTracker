# Project Roadmap

This document outlines the high-level roadmap for the ColorTracker project, focusing on performance, architecture, and feature expansion.

## Phase 1-3: Quality of Life & UX (Completed)
*See [plans/qol_improvement_plan.md](qol_improvement_plan.md) for details.*

## Phase 4: Hyper-Speed Capture (DXGI)
- **Objective**: Move from CPU Capture (MSS) to GPU Capture (DXGI).
- **Target**: 240Hz - 960Hz tracking support.
- **Status**: Architecture Design Phase.
- **Details**:
    - Replace `mss` with `python-dxcam` or direct DXGI Desktop Duplication API.
    - Implement zero-copy buffer handling where possible.
    - Refactor `DetectionSystem` to use abstract `CaptureBackend`.
    - Benchmarking target: < 1ms capture time at 1080p.

## Phase 5: Advanced Polish (Deferred)
*Previously Phase 4 of QoL Plan.*
- Enhanced Tooltips.
- Slider Step Snapping.
- STATS CSV Export.

## Phase 6: Cleanup & Verification (Deferred)
*Previously Phase 5 of QoL Plan.*
- Dead Code Removal.
- Final QA Gate.
