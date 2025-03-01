from pynput.keyboard import Key, KeyCode
from typing import Literal
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController, Button
import subprocess
import sys

# fmt: off
KeyboardKey = Literal[
    "a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s",
    "t","u","v","w","x","y","z","1","2","3","4","5","6","7","8","9","0","ä","ö",
    "ü","ß","!",'"',"$","%","&","/","(",")","=","?","'","+","#","-",".",",","*",
    "'","_",":",";","<",">","|","{","[","]","}","\\","~","@","€","^","`","°",
    "space","enter","tab","backspace","alt","ctrl","shift","cmd","up","down",
    "left","right","esc"
]
"""A key on the keyboard."""
# fmt: on


def string_to_pynput_compatible(key: KeyboardKey) -> Key | str:
    """Convert a string to a pynput compatible key."""
    if key == "space":
        return Key.space
    elif key == "enter":
        return Key.enter
    elif key == "tab":
        return Key.tab
    elif key == "backspace":
        return Key.backspace
    elif key == "alt":
        return Key.alt
    elif key == "ctrl":
        return Key.ctrl
    elif key == "shift":
        return Key.shift
    elif key == "cmd":
        return Key.cmd
    elif key == "up":
        return Key.up
    elif key == "down":
        return Key.down
    elif key == "left":
        return Key.left
    elif key == "right":
        return Key.right
    elif key == "esc":
        return Key.esc


SIMPLE_CHARS: list[KeyboardKey] = list("123456789abcdefghijklmnopqrstuvwxyz ")
MODIFIERS: list[KeyboardKey] = ["shift", "ctrl", "alt", "cmd"]
SPECIAL_KEYS: list[KeyboardKey] = [
    "space",
    "enter",
    "tab",
    "backspace",
    "alt",
    "ctrl",
    "shift",
    "cmd",
    "up",
    "down",
    "left",
    "right",
    "esc",
]


MouseButtonName = Literal["left", "middle", "right"]

has_xdotool = False


def check_xdotool_installation():
    global has_xdotool
    if has_xdotool:
        return

    if sys.platform == "linux":
        try:
            subprocess.run(["xdotool", "--version"], check=True)
            has_xdotool = True
        except Exception:
            print(
                "xdotool not found. Please install for better special character typing support by running 'sudo apt install xdotool'"
            )


class Keyboard:
    def __init__(self):
        check_xdotool_installation()
        self.keyboard = KeyboardController()

    def type(self, text: str):
        self.keyboard.type(text)

    def press(self, key: KeyboardKey):
        if key in SPECIAL_KEYS or key in MODIFIERS:
            self.keyboard.press(string_to_pynput_compatible(key))
        elif key in SIMPLE_CHARS or not has_xdotool:
            self.keyboard.press(key)
        else:
            subprocess.run(["xdotool", "type", key])

    def release(self, key: KeyboardKey):
        if key in SPECIAL_KEYS or key in MODIFIERS:
            self.keyboard.release(string_to_pynput_compatible(key))
        elif key in SIMPLE_CHARS or not has_xdotool:
            self.keyboard.release(key)


class Mouse:
    def __init__(self):
        check_xdotool_installation()
        self.mouse = MouseController()

    def press(self, button: MouseButtonName):
        if button == "left":
            button = Button.left
        elif button == "middle":
            button = Button.middle
        elif button == "right":
            button = Button.right
        self.mouse.press(button)

    def release(self, button: MouseButtonName):
        if button == "left":
            button = Button.left
        elif button == "middle":
            button = Button.middle
        elif button == "right":
            button = Button.right
        self.mouse.release(button)

    def move(self, x: int, y: int):
        if x != 0 or y != 0:
            self.mouse.move(x, y)

    def scroll(self, x: int, y: int):
        if x != 0 or y != 0:
            self.mouse.scroll(x, y)
