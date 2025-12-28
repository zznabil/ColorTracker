# Release Notes - SAI Color Tracker Algorithm V3.2.3 (Gem Harvest Release)

**V3.2.3** represents the culmination of a deep architectural analysis ("Gem Harvesting"), reuniting the production codebase with valuable optimizations discovered in experimental branches.

## 💎 Gem Harvest Optimizations
This release integrates elite performance features audited for clinical precision:

### 1. Orchestration Overhaul (`main.py`)
- **Method Caching**: Bypasses `self.` lookup overhead in the hot-loop.
- **Hybrid Sync**: Nanosecond-accurate frame timing combining sleep and spin-wait logic.

### 2. FOV & Bound Caching (`core/detection.py`)
- **What**: Caches screen boundaries and color conversion bounds.
- **Impact**: Eliminates ~30 attribute lookups and arithmetic operations **per frame**.

### 3. INPUT Structure Reuse (`core/low_level_movement.py`)
- **What**: Caches the Windows `ctypes.INPUT` C-structure.
- **Impact**: Zero memory allocation during rapid mouse movement.

## 🛡 Quality Assurance
- **New Test Suite**: Added `tests/test_low_level_movement_opt.py` to permanently verify the input reuse optimization.
- **Regression Testing**: Validated against the existing test suite (Compass) to ensure no functionality was lost during the merge.

---
*The "Universal Architect" has spoken: The repository is now clean, unified, and fully optimized.*
