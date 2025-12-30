import ctypes
import threading
import time
from ctypes import wintypes


# --- Structures ---
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

# --- Constants ---
WH_MOUSE_LL = 14
WM_MOUSEMOVE = 0x0200
LLMHF_INJECTED = 0x00000001
LLMHF_LOWER_IL_INJECTED = 0x00000002

# --- Globals ---
stop_event = threading.Event()

# Define CallNextHookEx with correct types
CallNextHookEx = ctypes.windll.user32.CallNextHookEx
CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
CallNextHookEx.restype = ctypes.c_long

def validator_hook_proc(nCode, wParam, lParam):
    if nCode >= 0 and wParam == WM_MOUSEMOVE:
        info_ptr = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT))
        info = info_ptr.contents

        flags = info.flags
        status = "CLEAN"
        color_code = "\033[92m" # Green

        if flags & LLMHF_INJECTED:
            status = "DETECTED (Injected)"
            color_code = "\033[91m" # Red
            print(f"{color_code}[EVENT] MouseMove | Flags: {flags:#010b} | Status: {status}\033[0m")
        elif flags & LLMHF_LOWER_IL_INJECTED:
            status = "DETECTED (Lower IL)"
            color_code = "\033[91m" # Red
            print(f"{color_code}[EVENT] MouseMove | Flags: {flags:#010b} | Status: {status}\033[0m")
        # else: print clean? No, reduce noise.

    return CallNextHookEx(None, nCode, wParam, lParam)


def start_validator():
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
    proc = HOOKPROC(validator_hook_proc)

    h_mod = kernel32.GetModuleHandleW(None)
    h_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, proc, h_mod, 0)

    if not h_hook:
        print(f"Failed with hMod=GetModuleHandle(None), Error: {ctypes.GetLastError()}")
        # Try NULL
        h_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, proc, 0, 0)

    if not h_hook:
        error = ctypes.GetLastError()
        print(f"Failed to install hook with NULL. Error Code: {error}")
        return

    print("Validator Active. Monitoring Mouse Flags... (Press Ctrl+C to stop)")
    print("----------------------------------------------------------------")

    msg = wintypes.MSG()
    while not stop_event.is_set():
        if user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1): # PM_REMOVE
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        time.sleep(0.001) # Avoid 100% CPU

    user32.UnhookWindowsHookEx(h_hook)

if __name__ == "__main__":
    try:
        start_validator()
    except KeyboardInterrupt:
        stop_event.set()
