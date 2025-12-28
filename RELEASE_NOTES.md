# Release Notes - SAI Color Tracker Algorithm V3.2.3 (Gem Harvest Release)

**V3.2.3** represents the culmination of a deep architectural analysis ("Gem Harvesting"), reuniting the production codebase with valuable optimizations discovered in experimental branches.

## 💎 Gem Harvest Optimizations
This release integrates high-value features previously isolated in experimental sessions:

### 1. FOV Caching (`core/detection.py`)
- **What**: Caches screen center and FOV boundary calculations.
- **Why**: Eliminates ~20 attribute lookups and arithmetic operations **per frame** in the critical detection loop.
- **Impact**: Measurable reduction in CPU usage during high-speed tracking.

### 2. INPUT Structure Reuse (`core/low_level_movement.py`)
- **What**: Caches the Windows `ctypes.INPUT` C-structure instead of recreating it for every mouse event.
- **Why**: Prevents continuous memory allocation and garbage collection overhead during rapid mouse movement.
- **Impact**: Smoother, more consistent mouse response with reduced micro-stutters.

## 🛡 Quality Assurance
- **New Test Suite**: Added `tests/test_low_level_movement_opt.py` to permanently verify the input reuse optimization.
- **Regression Testing**: Validated against the existing test suite (Compass) to ensure no functionality was lost during the merge.

---
*The "Universal Architect" has spoken: The repository is now clean, unified, and fully optimized.*
