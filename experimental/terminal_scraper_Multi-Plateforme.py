import os
import re
import sys
import time
import psutil
import pyautogui
import pyperclip

# Conditional Windows imports so the script doesn't crash on macOS / Linux
if sys.platform == "win32":
    import win32gui
    import win32process

pyautogui.PAUSE = 0.02

# Cross-platform terminal profiles
WINDOWS_TERMINALS = {
    "windowsterminal.exe": "wt",
    "code.exe": "wt",
    "wezterm-gui.exe": "wt",
    "alacritty.exe": "wt",
    "hyper.exe": "wt",
    "cmd.exe": "conhost",
    "powershell.exe": "conhost",
    "pwsh.exe": "conhost",
    "mintty.exe": "mintty",
}

LINUX_TERMINALS = {
    "gnome-terminal-server", "konsole", "xfce4-terminal",
    "alacritty", "kitty", "wezterm-gui", "terminator", "tilix", "code"
}

MAC_TERMINALS = {
    "Terminal", "iTerm2", "Alacritty", "kitty", "WezTerm", "Code", "Hyper"
}

# Universal Prompt Regex:
# Supports optional (venv)/(conda), PowerShell, CMD, Bash ($/#), macOS Zsh (%), and Starship/OhMyZsh (➜/❯)
PROMPT_PATTERN = re.compile(
    r'^(?:\([\w\.\-\+]+\)\s*)*'
    r'(?:'
    r'PS\s+[A-Za-z]:\\[^>]*>|'                  # PowerShell: PS C:\path>
    r'[A-Za-z]:\\[^>]*>|'                       # CMD: C:\path>
    r'[\w\.\-]+@[\w\.\-]+[:\s][^$#%❯➜]*[$#%❯➜]|' # Bash / Zsh: user@host:~$ or user@mac ~ %
    r'(?:➜|❯)\s+[^\s]+\s*'                      # Oh-My-Zsh / Starship minimal prompt
    r')\s*(.*)$'
)

SCRIPT_NAME = os.path.basename(__file__)


def get_terminal_mode():
    """Detects the OS and active terminal, returning the appropriate copy strategy."""
    if sys.platform == "win32":
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            exe_name = psutil.Process(pid).name().lower()
            return WINDOWS_TERMINALS.get(exe_name)
        except Exception:
            return None

    elif sys.platform == "darwin":
        # macOS uses Command+A / Command+C
        return "mac"

    elif sys.platform.startswith("linux"):
        # Linux GUI terminals use Ctrl+Shift+A / Ctrl+Shift+C
        return "linux"

    return None


def copy_from_terminal(mode):
    """Triggers the native Select-All + Copy + Scroll-to-Bottom for each OS/Terminal."""
    if mode in ("wt", "linux"):
        pyautogui.hotkey('ctrl', 'shift', 'a')
        time.sleep(0.03)
        pyautogui.hotkey('ctrl', 'shift', 'c')
        pyautogui.hotkey('ctrl', 'shift', 'end')
    elif mode == "conhost":
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.03)
        pyautogui.press('enter')
    elif mode == "mintty":
        pyautogui.hotkey('ctrl', 'shift', 'a')
        time.sleep(0.03)
        pyautogui.hotkey('ctrl', 'insert')
    elif mode == "mac":
        pyautogui.hotkey('command', 'a')
        time.sleep(0.04)
        pyautogui.hotkey('command', 'c')
        pyautogui.hotkey('command', 'down')


def extract_last_thing():
    """Scans the terminal buffer from bottom to top and copies only the last command + output."""
    raw_text = pyperclip.paste()
    if not raw_text:
        return False

    lines = raw_text.splitlines()
    end_idx = len(lines)

    # Scan from BOTTOM to TOP for O(1) speed on recent output
    for i in range(len(lines) - 1, -1, -1):
        match = PROMPT_PATTERN.match(lines[i])
        if match:
            cmd = match.group(1).strip()

            # Ignore the scraper command itself and any empty prompts at the bottom
            if SCRIPT_NAME in cmd or not cmd:
                end_idx = i
                continue

            # Found the target command: slice from here to end_idx and copy
            result = "\n".join(line.rstrip() for line in lines[i:end_idx]).rstrip()
            pyperclip.copy(result)
            return True

    # Fallback: If output exceeded scrollback buffer and pushed prompt off the top
    if end_idx > 0:
        result = "\n".join(line.rstrip() for line in lines[0:end_idx]).rstrip()
        if result:
            pyperclip.copy(result)
            return True

    return False


if __name__ == "__main__":
    mode = get_terminal_mode()
    if not mode:
        sys.exit(0)

    copy_from_terminal(mode)
    if extract_last_thing():
        print("✅ Copied last command + output to clipboard!")
    sys.exit(0)