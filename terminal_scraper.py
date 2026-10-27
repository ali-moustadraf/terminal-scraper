import sys
import time
import re
import psutil
import win32gui
import win32process
import pyautogui
import pyperclip

ALLOWED_TERMINALS = {
    "windowsterminal.exe": "wt",
    "cmd.exe": "conhost",
    "powershell.exe": "conhost",
    "pwsh.exe": "conhost",
    "code.exe": "wt",
}

# Pre-compile regex once for speed
PROMPT_PATTERN = re.compile(
    r'^(?:PS\s+[A-Z]:\\[^>]*>|[A-Z]:\\[^>]*>|[\w\.-]+@[\w\.-]+:[^$#]*[$#])\s*(.*)$'
)

def get_active_exe():
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return ""
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        return psutil.Process(pid).name().lower()
    except Exception:
        return ""

pyautogui.PAUSE = 0.02  # Overrides pyautogui's default 0.1s delay per action

def copy_from_terminal(term_type):
    if term_type == "wt":
        pyautogui.hotkey('ctrl', 'shift', 'a')
        time.sleep(0.03)  # Tiny gap just so Windows Terminal registers the highlight
        pyautogui.hotkey('ctrl', 'shift', 'c')
        pyautogui.hotkey('ctrl', 'shift', 'end')  # Snap scrollbar back to the bottom
    elif term_type == "conhost":
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.03)
        pyautogui.press('enter')

def extract_last_thing():
    raw_text = pyperclip.paste()
    if not raw_text:
        return False

    lines = raw_text.splitlines()
    end_idx = len(lines)

    # Scan from BOTTOM to TOP
    for i in range(len(lines) - 1, -1, -1):
        match = PROMPT_PATTERN.match(lines[i])
        if match:
            cmd = match.group(1).strip()

            # Ignore the scraper command itself and any empty prompts at the bottom
            if "terminal_scraper.py" in cmd or not cmd:
                end_idx = i
                continue

            # Found the last real command! Slice from here to end_idx and stop immediately
            result = "\n".join(line.rstrip() for line in lines[i:end_idx]).rstrip()
            pyperclip.copy(result)
            return True

    # Fallback: If output was so huge that the prompt scrolled off the top, copy all visible lines
    if end_idx > 0:
        result = "\n".join(line.rstrip() for line in lines[0:end_idx]).rstrip()
        if result:
            pyperclip.copy(result)
            return True

    return False

if __name__ == "__main__":
    active_exe = get_active_exe()

    if active_exe not in ALLOWED_TERMINALS:
        sys.exit(0)

    copy_from_terminal(ALLOWED_TERMINALS[active_exe])
    if extract_last_thing():
        print("✅ Copied last command + output to clipboard!")
    sys.exit(0)