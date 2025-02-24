import os
import json
from typing import Literal

filename = "best_mapping.json"

ControllerButton = Literal[
    "face_up",
    "face_down",
    "face_left",
    "face_right",
    "shoulder_l",
    "shoulder_r",
    "shoulder_zl",
    "shoulder_zr",
]

if os.path.exists(filename):
    with open(filename, "r") as f:
        _best_map: dict[str, list[ControllerButton]] = json.load(f)
else:
    exit(1)

best_map: dict[str, set[ControllerButton]] = {}
for key, value in _best_map.items():
    best_map[key] = set(value)

# Convert to the following string format
"""
[
    MultiControllerButtonAction(
        buttons=["shoulder_r", "face_up"],
        actions={
            "down": ComputerKeyDownAction(key="l"),
            "up": ComputerKeyUpAction(key="l"),
        },
    ),
]
"""

output = []
for key, buttons in best_map.items():
    buttons_string = ", ".join([f'"{button}"' for button in buttons])
    s = "MultiControllerButtonAction(\n"
    s += f"    buttons=[{buttons_string}],\n"
    s += "    actions={\n"
    s += f'        "down": ComputerKeyDownAction(key="{key}"),\n'
    s += f'        "up": ComputerKeyUpAction(key="{key}"),\n'
    s += "    },\n"
    s += ")"
    output.append(s)

o = ",\n".join(output)

with open("best_mapping.py", "w") as f:
    f.write(o)