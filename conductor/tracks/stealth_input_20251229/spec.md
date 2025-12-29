# Specification: Deep Stealth - Input Integrity (Stealth Engines)

## 1. Overview
Implement an interchangeable movement engine system to support high-stealth injection methods. The primary goal is to bypass the LLMHF_INJECTED flag using methods that do not require custom kernel drivers.

## 2. Functional Requirements
- **Interchangeable Engine Core:** Refactor LowLevelMovementSystem into a strategy pattern.
- **Engine A (Standard):** Current SendInput logic (Reliability fallback).
- **Engine B (Logitech Proxy):** Attempt to use logitech_g_hub or lghub_agent DLLs to proxy input through a signed, whitelisted driver.
- **Engine C (Flag Masker):** Implement a WH_MOUSE_LL hook to attempt clearing the injected flag from the system input queue.
- **System Tab UI:** Add a "Stealth Engine" dropdown to select the active method.
- **Auto-Validation:** Each engine must perform a "Self-Test" on activation to verify if the required environment (e.g., Logitech software) is present.

## 3. Non-Functional Requirements
- **Sub-ms Latency:** Switching engines must not introduce jitter.
- **Zero-Allocation:** Engine logic must adhere to Archetype A standards.

## 4. Acceptance Criteria
- GUI (System Tab) allows switching between engines.
- Tooltips or logs indicate whether a stealth engine successfully initialized.
- Mouse movement remains precise across all engines.
