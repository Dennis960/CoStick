import pygame
from pygame.locals import *
from typing import Callable, Optional, List, Tuple, Self
from dataclasses import dataclass
import time
from config import *


class Button:
    def __init__(
        self, name: str, index: ControllerButtonIndex, settings: ControllerSettings
    ):
        self.name = name
        self.index: ControllerButtonIndex = index
        self.pressed = False
        self.long_pressed = False

        # internal properties
        self._pressed_time_start = 0  # Time when the button was last pressed in seconds
        self._pressed_time_end = 0  # Time when the button was last released in seconds
        self._last_click_time = 0  # Time of the release of the last click in seconds
        self._last_double_click_time = 0  # Time of the last double click in seconds
        self._settings = settings

        # Event listeners
        self.event_listeners: list[
            tuple[ControllerButtonEventName, Callable[[Self], None]]
        ] = []

    def add_event_listener(
        self,
        controller_button_event_name: ControllerButtonEventName,
        listener: Callable[[Self], None],
    ):
        """Add a listener for the given event."""
        self.event_listeners.append((controller_button_event_name, listener))

    def get_event_listeners(
        self, controller_button_event_name: ControllerButtonEventName
    ):
        """Get all listeners for the given event."""
        return [
            listener
            for event_name, listener in self.event_listeners
            if event_name == controller_button_event_name
        ]

    def call_event_listeners(
        self, controller_stick_event_name: ControllerStickEventName
    ):
        """Call all listeners for the given event in the order they were added."""
        for listener in self.get_event_listeners(controller_stick_event_name):
            listener(self)

    def remove_all_event_listeners(self):
        """Remove all event listeners"""
        self.event_listeners = []

    def _down(self):
        """Has to be called when the button is pressed down"""
        self.pressed = True
        self._pressed_time_start = time.time()
        self.call_event_listeners("down")

        if (
            self._pressed_time_start - self._last_double_click_time
            <= self._settings.double_click_duration
        ):
            self.call_event_listeners("triple_click")
            self._last_double_click_time = 0
            self._last_click_time = 0
        elif (
            self._pressed_time_start - self._last_click_time
            <= self._settings.double_click_duration
        ):
            self.call_event_listeners("double_click")

    def _up(self):
        """Has to be called when the button is released"""
        self.pressed = False
        self.long_pressed = False
        self._pressed_time_end = time.time()

        self.call_event_listeners("up")

        press_duration = self._pressed_time_end - self._pressed_time_start

        if press_duration > self._settings.single_click_duration:
            self.call_event_listeners("long_press")
        else:
            self.call_event_listeners("click")
            self._last_click_time = self._pressed_time_end

    def _update(self):
        """Has to be called every frame"""
        if self.pressed and not self.long_pressed:
            press_duration = time.time() - self._pressed_time_start
            if press_duration > self._settings.single_click_duration:
                self.long_pressed = True
                self.call_event_listeners("long_press_start")

    def __str__(self):
        return self.name


class Stick:
    def __init__(
        self,
        name: str,
        axis_x_index: int,
        axis_y_index: int,
        settings: ControllerSettings,
    ):
        self.name = name
        self.axis_x_index = axis_x_index
        self.axis_y_index = axis_y_index
        self._settings = settings
        self.x = 0
        self.y = 0

        # Event listeners
        self.event_listeners: list[
            tuple[ControllerStickEventName, Callable[[Self], None]]
        ] = []

    def add_event_listener(
        self,
        controller_stick_event_name: ControllerStickEventName,
        listener: Callable[[Self], None],
    ):
        """Add a listener for the given event."""
        self.event_listeners.append((controller_stick_event_name, listener))

    def get_event_listeners(
        self, controller_stick_event_name: ControllerStickEventName
    ):
        """Get all listeners for the given event."""
        return [
            listener
            for event_name, listener in self.event_listeners
            if event_name == controller_stick_event_name
        ]

    def call_event_listeners(
        self, controller_stick_event_name: ControllerStickEventName
    ):
        """Call all listeners for the given event in the order they were added."""
        for listener in self.get_event_listeners(controller_stick_event_name):
            listener(self)

    def remove_all_event_listeners(self):
        """Remove all listeners"""
        self.event_listeners = []

    def _move_x(self, value):
        """Has to be called when the joystick axis changes value. Ignores movements within the deadzone. Does not ignore going into and out of the deadzone."""
        if abs(value) > self._settings.deadzone:
            new_x = value
        else:
            if self.x != 0:
                new_x = 0
            else:
                return
        self.x = new_x
        self.call_event_listeners("move")

    def _move_y(self, value):
        """Has to be called when the joystick axis changes value. Ignores movements within the deadzone. Does not ignore going into and out of the deadzone."""
        if abs(value) > self._settings.deadzone:
            new_y = value
        else:
            if self.y != 0:
                new_y = 0
            else:
                return
        self.y = new_y
        self.call_event_listeners("move")

    def __str__(self):
        return self.name


class Controller:
    Stick = Stick
    Button = Button

    def __init__(self, config: Config):
        # Initialize Pygame
        pygame.init()

        self.config = config
        self.buttons: dict[ControllerButtonName, Button] = {}
        self.sticks: dict[ControllerStickName, Stick] = {}
        for (
            controller_button_name,
            controller_button_index,
        ) in config.button_mapping.items():
            button = Button(
                name=controller_button_name,
                index=controller_button_index,
                settings=config.settings.controller_settings,
            )
            self.buttons |= {controller_button_name: button}

        for controller_stick_name, (
            axis_x_index,
            axis_y_index,
        ) in config.stick_mapping.items():
            stick = Stick(
                name=controller_stick_name,
                axis_x_index=axis_x_index,
                axis_y_index=axis_y_index,
                settings=config.settings.controller_settings,
            )
            self.sticks |= {controller_stick_name: stick}

        self.pygame_controller = None

        # Event listeners
        self._on_multi_button: List[Callable[[list[Button]], None]] = []

    def handle_joy_disconnect(self):
        print("Controller disconnected")
        self.pygame_controller = None

    def handle_joy_connect(self):
        if not self.pygame_controller:
            self.pygame_controller = self.get_connected_controller()
            if self.pygame_controller:
                print(f"controller connected: {self.pygame_controller.get_name()}")

    def handle_joy_axis_motion(self, event: pygame.event.Event):
        assert event.type == JOYAXISMOTION
        axis: int = event.axis
        value: float = event.value
        for stick in self.sticks.values():
            if axis == stick.axis_x_index:
                stick._move_x(value)
            elif axis == stick.axis_y_index:
                stick._move_y(value)

    def handle_joy_button_down(self, event: pygame.event.Event):
        assert event.type == JOYBUTTONDOWN
        button_index: int = event.button
        for button in self.buttons.values():
            if button.index == button_index:
                button._down()

    def handle_joy_button_up(self, event: pygame.event.Event):
        assert event.type == JOYBUTTONUP
        button_index: int = event.button
        for button in self.buttons.values():
            if button.index == button_index:
                button._up()

    def handle_joy_hat_motion(self, event: pygame.event.Event):
        assert event.type == JOYHATMOTION
        value: tuple[int, int] = event.value
        for button in self.buttons.values():
            if button.index == "dpad+x" and value[0] == 1 and not button.pressed:
                button._down()
            if button.index == "dpad-x" and value[0] == -1 and not button.pressed:
                button._down()
            if button.index == "dpad+y" and value[1] == -1 and not button.pressed:
                button._down()
            if button.index == "dpad-y" and value[1] == 1 and not button.pressed:
                button._down()
            if button.index == "dpad+x" and value[0] == 0 and button.pressed:
                button._up()
            if button.index == "dpad-x" and value[0] == 0 and button.pressed:
                button._up()
            if button.index == "dpad+y" and value[1] == 0 and button.pressed:
                button._up()
            if button.index == "dpad-y" and value[1] == 0 and button.pressed:
                button._up()

    def run(self) -> None:
        # Initialize the controller
        pygame.joystick.init()
        self.handle_joy_connect()

        self.last_joy_connection_check = time.time()
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == JOYAXISMOTION:
                    self.handle_joy_axis_motion(event)
                elif event.type == JOYBUTTONDOWN:
                    self.handle_joy_button_down(event)
                elif event.type == JOYBUTTONUP:
                    self.handle_joy_button_up(event)
                elif event.type == JOYHATMOTION:
                    self.handle_joy_hat_motion(event)
                elif event.type == JOYDEVICEREMOVED:
                    self.handle_joy_disconnect()
                elif event.type == JOYDEVICEADDED:
                    self.handle_joy_connect()
            if (
                not self.pygame_controller
                and time.time() - self.last_joy_connection_check > 1
            ):
                self.handle_joy_connect()
                continue
            time.sleep(0)
        # Quit Pygame
        pygame.quit()

    def get_connected_controller(self) -> pygame.joystick.JoystickType | None:
        # Check for controller
        if pygame.joystick.get_count() == 0:
            return None

        # Get the first controller
        controller = pygame.joystick.Joystick(0)
        controller.init()
        return controller

    def add_multi_button_event_listener(
        self,
        controller_button_event_name: ControllerButtonEventName,
        controller_button_names: list[ControllerButtonName],
        listener: Callable[[list[Button]], None],
    ):
        """Add a listener for the multi button event."""
        self._on_multi_button.append(listener)

    def remove_all_event_listeners(self):
        for button in self.buttons.values():
            button.remove_all_event_listeners()
        for stick in self.sticks.values():
            stick.remove_all_event_listeners()
        self._on_multi_button = []


if __name__ == "__main__":
    from config import default_config

    controller = Controller(default_config)
    for button in controller.buttons.values():
        button.add_event_listener(
            "click", lambda button: print(f"Button {button} clicked")
        )
    for stick in controller.sticks.values():
        stick.add_event_listener(
            "move", lambda stick: print(f"Stick {stick} moved to {stick.x}, {stick.y}")
        )
    # controller.gestures.on_multi_click = lambda buttons: print(
    #     f"Buttons {buttons} clicked at the same time"
    # )  # Called when multiple buttons are pressed at the same time as soon as all buttons are released again

    controller.run()
