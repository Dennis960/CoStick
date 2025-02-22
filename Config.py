from pydantic import BaseModel
from typing import Literal


KeyboardKey = str
"""A key on the keyboard. For example: "a", "b", "c", "1", "2", "3", "up", "down", "left", "right" etc."""
MouseButton = Literal["left", "middle", "right"]
"""A mouse button."""
ControllerButton = Literal[
    "dpad_up",
    "dpad_down",
    "dpad_left",
    "dpad_right",
    "face_up",
    "face_down",
    "face_left",
    "face_right",
    "shoulder_l",
    "shoulder_r",
    "shoulder_zl",
    "shoulder_zr",
    "stick_left",
    "stick_right",
    "minus",
    "plus",
    "home",
    "capture",
]
"""A button on the controller."""
ControllerStick = Literal["stick_left", "stick_right"]
"""A stick on the controller."""
ControllerButtonEventType = Literal[
    "down", "up", "click", "long_press", "double_click", "tripple_click"
]
"""An event type for a button of the controller being pressed or released."""
ControllerStickEventType = Literal["move"]
"""An event type for a stick of the controller being moved."""


class ControllerSettings(BaseModel):
    """Settings for the controller."""

    deadzone: float
    """Deadzone for the controller's sticks."""
    single_click_duration: float
    """Delay in seconds between a controler's button press and release to be registered as a single click."""
    double_click_duration: float
    """Delay in seconds between the release of the last single_click and the new press of the same button on the controller to be registered as a double click."""
    multi_click_duration: float
    """Maximum time in seconds starting from the first press of any button during which more button presses are added to the multi-click event before firing the event."""


class CursorSettings(BaseModel):
    """Settings for the cursor."""

    cursor_speed_pixels_per_second: int
    """Cursor will move at this speed in normal mode"""
    cursor_boost_speed: int
    """Cursor will move at this speed when boosting"""
    cursor_boost_acceleration_delay: float
    """Cursor will wait for this time before boosting"""
    cursor_boost_acceleration_time: float
    """Cursor will take this time to reach the boost speed"""
    scroll_speed: float
    """Speed of scrolling"""


class Settings(BaseModel):
    """Settings for the application."""

    controller: ControllerSettings
    cursor: CursorSettings


class ComputerKeyDownAction(BaseModel):
    """Action to press a key on the computer."""

    action: str = "key_down"
    key: KeyboardKey


class ComputerKeyUpAction(BaseModel):
    """Action to release a key on the computer."""

    action: str = "key_up"
    key: KeyboardKey


class ComputerMouseMoveAction(BaseModel):
    """Action to move the mouse."""

    action: str = "mouse_move"


class ComputerMouseDownAction(BaseModel):
    """Action to press the mouse button."""

    action: str = "mouse_down"
    button: MouseButton


class ComputerMouseUpAction(BaseModel):
    """Action to release the mouse button."""

    action: str = "mouse_up"
    button: MouseButton


class ComputerScrollAction(BaseModel):
    """Action to scroll the computer."""

    action: str = "scroll"


class SwitchModeAction(BaseModel):
    """Action to switch the mode of the application."""

    action: str = "switch_mode"
    mode: Literal["default"] | str


class ComputerTypeAction(BaseModel):
    """Action to type text on the computer."""

    action: str = "type"
    text: str


ComputerAction = (
    ComputerKeyDownAction
    | ComputerKeyUpAction
    | ComputerMouseDownAction
    | ComputerMouseUpAction
    | ComputerTypeAction
    | SwitchModeAction
)
"""Represents a single discrete action that can be performed on the computer."""
ComputerNavigation = ComputerMouseMoveAction | ComputerScrollAction | SwitchModeAction
"""Represents a continuous navigation action that can be performed on the computer."""


class MultiControllerButtonAction(BaseModel):
    """
    Defines a set of actions to be performed when a set of buttons are pressed or released during a multi-button event.
    """

    buttons: list[ControllerButton]
    actions: dict[ControllerButtonEventType, ComputerAction | list[ComputerAction]]


class Mode(BaseModel):
    """
    Represents the currently selected mode of control.
    Each mode specifies its own set of actions for events happening on the controller.
    """

    button_actions: (
        dict[
            ControllerButton,
            dict[ControllerButtonEventType, ComputerAction | list[ComputerAction]],
        ]
        | None
    ) = None
    stick_actions: (
        dict[
            ControllerStick,
            dict[
                ControllerStickEventType, ComputerNavigation | list[ComputerNavigation]
            ],
        ]
        | None
    ) = None
    multi_button_actions: list[MultiControllerButtonAction] | None = None


class Config(BaseModel):
    settings: Settings
    button_mapping: dict[
        ControllerButton, int | Literal["dpad-y", "dpad+y", "dpad-x", "dpad+x"]
    ]
    """Mapping of controller buttons to their respective index used by pygame or the axis of the dpad for the dpad buttons."""
    stick_mapping: dict[ControllerStick, tuple[int, int]]
    """Mapping of controller sticks to their respective axis indices used by pygame."""
    modes: dict[str, Mode]
    """Mapping of mode names to their respective mode configurations."""


config = Config(
    settings=Settings(
        controller=ControllerSettings(
            deadzone=0.1,
            single_click_duration=0.6,
            double_click_duration=0.2,
            multi_click_duration=0.2,
        ),
        cursor=CursorSettings(
            cursor_speed_pixels_per_second=800,
            cursor_boost_speed=5,
            cursor_boost_acceleration_delay=0.2,
            cursor_boost_acceleration_time=0.5,
            scroll_speed=0.5,
        ),
    ),
    button_mapping={
        "dpad_up": "dpad-y",
        "dpad_down": "dpad+y",
        "dpad_left": "dpad-x",
        "dpad_right": "dpad+x",
        "face_down": 0,
        "face_right": 1,
        "face_up": 2,
        "face_left": 3,
        "shoulder_l": 5,
        "shoulder_r": 6,
        "shoulder_zl": 7,
        "shoulder_zr": 8,
        "stick_left": 12,
        "stick_right": 13,
    },
    stick_mapping={
        "stick_left": (0, 1),
        "stick_right": (2, 3),
    },
    modes={
        "default": Mode(
            button_actions={
                "dpad_up": {
                    "down": ComputerKeyDownAction(key="up"),
                    "up": ComputerKeyUpAction(key="up"),
                },
                "dpad_down": {
                    "down": ComputerKeyDownAction(key="down"),
                    "up": ComputerKeyUpAction(key="down"),
                },
                "dpad_left": {
                    "down": ComputerKeyDownAction(key="left"),
                    "up": ComputerKeyUpAction(key="left"),
                },
                "dpad_right": {
                    "down": ComputerKeyDownAction(key="right"),
                    "up": ComputerKeyUpAction(key="right"),
                },
                "face_right": {
                    "down": ComputerMouseDownAction(button="left"),
                    "up": ComputerMouseUpAction(button="left"),
                },
                "face_down": {
                    "down": ComputerMouseDownAction(button="right"),
                    "up": ComputerMouseUpAction(button="right"),
                },
                "stick_right": {
                    "down": ComputerMouseDownAction(button="middle"),
                    "up": ComputerMouseUpAction(button="middle"),
                },
                "minus": {
                    "down": [
                        ComputerKeyDownAction(key="ctrl"),
                        ComputerKeyDownAction(key="c"),
                    ],  # TODO create actions types for copy, paste, cut, ...
                    "up": [
                        ComputerKeyUpAction(key="ctrl"),
                        ComputerKeyUpAction(key="c"),
                    ],
                },
                "plus": {
                    "down": [
                        ComputerKeyDownAction(key="ctrl"),
                        ComputerKeyDownAction(key="v"),
                    ],
                    "up": [
                        ComputerKeyUpAction(key="ctrl"),
                        ComputerKeyUpAction(key="v"),
                    ],
                },
                "home": {
                    "down": [
                        SwitchModeAction(mode="default"),
                        ComputerKeyDownAction(key="esc"),
                    ],
                    "up": [
                        SwitchModeAction(mode="default"),
                        ComputerKeyUpAction(key="esc"),
                    ],
                },
                "shoulder_l": {
                    "click": SwitchModeAction(mode="typing"),
                },
            },
            stick_actions={
                "stick_left": {
                    "move": ComputerMouseMoveAction(),
                },
                "stick_right": {
                    "move": ComputerScrollAction(),
                },
            },
        ),
        "selection": Mode(
            button_actions={
                "face_right": {
                    "down": ComputerKeyDownAction(key="shift"),
                    "up": ComputerKeyUpAction(key="shift"),
                },
                "face_down": {
                    "down": ComputerKeyDownAction(key="ctrl"),
                    "up": ComputerKeyUpAction(key="ctrl"),
                },
            },
            stick_actions={
                "stick_right": {
                    "move": SwitchModeAction(mode="default"),
                },
                "stick_left": {
                    "move": SwitchModeAction(mode="default"),
                },
            },
        ),
        "typing": Mode(
            button_actions={
                "dpad_up": {
                    "down": ComputerKeyDownAction(key="shift"),
                    "up": ComputerKeyUpAction(key="shift"),
                },
                "dpad_left": {
                    "down": ComputerKeyDownAction(key="ctrl"),
                    "up": ComputerKeyUpAction(key="ctrl"),
                },
            },
            multi_button_actions=[
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "face_right"],
                    actions={
                        "down": ComputerKeyDownAction(key="a"),
                        "up": ComputerKeyUpAction(key="a"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "face_down"],
                    actions={
                        "down": ComputerKeyDownAction(key="b"),
                        "up": ComputerKeyUpAction(key="b"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "face_left"],
                    actions={
                        "down": ComputerKeyDownAction(key="c"),
                        "up": ComputerKeyUpAction(key="c"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "face_up"],
                    actions={
                        "down": ComputerKeyDownAction(key="d"),
                        "up": ComputerKeyUpAction(key="d"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zl", "face_right"],
                    actions={
                        "down": ComputerKeyDownAction(key="e"),
                        "up": ComputerKeyUpAction(key="e"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zl", "face_down"],
                    actions={
                        "down": ComputerKeyDownAction(key="f"),
                        "up": ComputerKeyUpAction(key="f"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zl", "face_left"],
                    actions={
                        "down": ComputerKeyDownAction(key="g"),
                        "up": ComputerKeyUpAction(key="g"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zl", "face_up"],
                    actions={
                        "down": ComputerKeyDownAction(key="h"),
                        "up": ComputerKeyUpAction(key="h"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_r", "face_right"],
                    actions={
                        "down": ComputerKeyDownAction(key="i"),
                        "up": ComputerKeyUpAction(key="i"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_r", "face_down"],
                    actions={
                        "down": ComputerKeyDownAction(key="j"),
                        "up": ComputerKeyUpAction(key="j"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_r", "face_left"],
                    actions={
                        "down": ComputerKeyDownAction(key="k"),
                        "up": ComputerKeyUpAction(key="k"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_r", "face_up"],
                    actions={
                        "down": ComputerKeyDownAction(key="l"),
                        "up": ComputerKeyUpAction(key="l"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zr", "face_right"],
                    actions={
                        "down": ComputerKeyDownAction(key="m"),
                        "up": ComputerKeyUpAction(key="m"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zr", "face_down"],
                    actions={
                        "down": ComputerKeyDownAction(key="n"),
                        "up": ComputerKeyUpAction(key="n"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zr", "face_left"],
                    actions={
                        "down": ComputerKeyDownAction(key="o"),
                        "up": ComputerKeyUpAction(key="o"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zr", "face_up"],
                    actions={
                        "down": ComputerKeyDownAction(key="p"),
                        "up": ComputerKeyUpAction(key="p"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_r", "face_right"],
                    actions={
                        "down": ComputerKeyDownAction(key="q"),
                        "up": ComputerKeyUpAction(key="q"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_r", "face_down"],
                    actions={
                        "down": ComputerKeyDownAction(key="r"),
                        "up": ComputerKeyUpAction(key="r"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_r", "face_left"],
                    actions={
                        "down": ComputerKeyDownAction(key="s"),
                        "up": ComputerKeyUpAction(key="s"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_r", "face_up"],
                    actions={
                        "down": ComputerKeyDownAction(key="t"),
                        "up": ComputerKeyUpAction(key="t"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zl", "shoulder_r", "face_right"],
                    actions={
                        "down": ComputerKeyDownAction(key="u"),
                        "up": ComputerKeyUpAction(key="u"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zl", "shoulder_r", "face_down"],
                    actions={
                        "down": ComputerKeyDownAction(key="v"),
                        "up": ComputerKeyUpAction(key="v"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zl", "shoulder_r", "face_left"],
                    actions={
                        "down": ComputerKeyDownAction(key="w"),
                        "up": ComputerKeyUpAction(key="w"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_zl", "shoulder_r", "face_up"],
                    actions={
                        "down": ComputerKeyDownAction(key="x"),
                        "up": ComputerKeyUpAction(key="x"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_zr", "face_right"],
                    actions={
                        "down": ComputerKeyDownAction(key="y"),
                        "up": ComputerKeyUpAction(key="y"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_zr", "face_down"],
                    actions={
                        "down": ComputerKeyDownAction(key="z"),
                        "up": ComputerKeyUpAction(key="z"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_zr", "face_left"],
                    actions={
                        "down": ComputerKeyDownAction(key="1"),
                        "up": ComputerKeyUpAction(key="1"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_zr", "face_up"],
                    actions={
                        "down": ComputerKeyDownAction(key="2"),
                        "up": ComputerKeyUpAction(key="2"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_r", "shoulder_zl", "face_right"],
                    actions={
                        "down": ComputerKeyDownAction(key="3"),
                        "up": ComputerKeyUpAction(key="3"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_r", "shoulder_zl", "face_down"],
                    actions={
                        "down": ComputerKeyDownAction(key="4"),
                        "up": ComputerKeyUpAction(key="4"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_r", "shoulder_zl", "face_left"],
                    actions={
                        "down": ComputerKeyDownAction(key="5"),
                        "up": ComputerKeyUpAction(key="5"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_r", "shoulder_zl", "face_up"],
                    actions={
                        "down": ComputerKeyDownAction(key="6"),
                        "up": ComputerKeyUpAction(key="6"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_r", "shoulder_zl", "face_right"],
                    actions={
                        "down": ComputerKeyDownAction(key="7"),
                        "up": ComputerKeyUpAction(key="7"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_r", "shoulder_zl", "face_down"],
                    actions={
                        "down": ComputerKeyDownAction(key="8"),
                        "up": ComputerKeyUpAction(key="8"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_r", "shoulder_zl", "face_left"],
                    actions={
                        "down": ComputerKeyDownAction(key="9"),
                        "up": ComputerKeyUpAction(key="9"),
                    },
                ),
                MultiControllerButtonAction(
                    buttons=["shoulder_l", "shoulder_r", "shoulder_zl", "face_up"],
                    actions={
                        "down": ComputerKeyDownAction(key="0"),
                        "up": ComputerKeyUpAction(key="0"),
                    },
                ),
            ],
        ),
    },
)


if __name__ == "__main__":
    with open("config.json", "w") as f:
        f.write(config.model_dump_json(indent=4))
    with open("config.json", "r") as f:
        new_config = Config.model_validate_json(f.read())
    assert config.model_dump() == new_config.model_dump(), "Config is not valid!"
    print("Config is valid!")
