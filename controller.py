import pygame
from pygame.locals import *
from typing import Callable, Self
import time
from config import *
import threading
import uuid
from event_listener import EventListener


class Button(EventListener[ControllerButtonEventName, "Button"]):
    def __init__(
        self, name: str, index: ControllerButtonIndex, settings: ControllerSettings
    ):
        super().__init__()

        self.name = name
        self.index: ControllerButtonIndex = index
        self.settings = settings

        # State
        self.pressed = False

        # Time tracking
        self.pressed_time_start = 0
        """Time when the button was last pressed in seconds"""
        self.pressed_time_end = 0
        """Time when the button was last released in seconds"""
        self.last_click_time = 0
        """Time of the release of the last click in seconds"""
        self.last_double_click_time = 0
        """Time of the last double click in seconds"""

    def _down(self):
        """Has to be called when the button is pressed down"""
        self.pressed = True
        self.pressed_time_start = time.time()
        self.call_event_listeners("down")

        if (
            self.pressed_time_start - self.last_double_click_time
            <= self.settings.double_click_duration
        ):
            self.call_event_listeners("tripple_click")
            self.last_double_click_time = 0
            self.last_click_time = 0
        elif (
            self.pressed_time_start - self.last_click_time
            <= self.settings.double_click_duration
        ):
            self.call_event_listeners("double_click")
            self.last_double_click_time = self.pressed_time_start

    def _up(self):
        """Has to be called when the button is released"""
        self.pressed = False
        self.pressed_time_end = time.time()

        self.call_event_listeners("up")

        press_duration = self.pressed_time_end - self.pressed_time_start

        if press_duration > self.settings.single_click_duration:
            self.call_event_listeners("long_press")
        else:
            self.call_event_listeners("click")
            self.last_click_time = self.pressed_time_end

    def __str__(self):
        return self.name


class Stick(EventListener[ControllerStickEventName, "Stick"]):
    def __init__(
        self,
        name: str,
        axis_x_index: int,
        axis_y_index: int,
        settings: ControllerSettings,
    ):
        super().__init__()

        self.name = name
        self.axis_x_index = axis_x_index
        self.axis_y_index = axis_y_index
        self.settings = settings

        # State
        self.x = 0
        self.y = 0

    def _move_x(self, value):
        """Has to be called when the joystick axis changes value. Ignores movements within the deadzone. Does not ignore going into and out of the deadzone."""
        if abs(value) > self.settings.deadzone:
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
        if abs(value) > self.settings.deadzone:
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


class MultiButtonEvents(
    EventListener[
        tuple[ControllerButtonEventName, list[ControllerButtonName]], list[Button]
    ]
):
    def get_event_listeners(self, event_trigger):
        event_name, event_button_names = event_trigger
        return [
            listener
            for (e_name, button_names), listener in self._event_listeners.values()
            if e_name == event_name and set(button_names) == set(event_button_names)
        ]

    def add_event_listener(
        self,
        controller_button_event_name: ControllerButtonEventName,
        controller_button_names: list[ControllerButtonName],
        listener: Callable[[list[Button]], None],
    ):
        """Add a listener for the multi button event."""
        return super().add_event_listener(
            (controller_button_event_name, controller_button_names), listener
        )

    def get_multi_button_event_listeners(
        self,
        controller_button_event_name: ControllerButtonEventName,
        buttons: list[Button],
    ):
        """Get all listeners for the given event."""
        return self.get_event_listeners(
            (
                controller_button_event_name,
                list([button.name for button in buttons]),
            )
        )

    def call_event_listeners(
        self,
        controller_button_event_name: ControllerButtonEventName,
        buttons: list[Button],
    ):
        """Call all listeners for the given event in the order they were added."""
        return super().call_event_listeners(
            (controller_button_event_name, [button.name for button in buttons]),
            buttons,
        )


class Controller:
    Stick = Stick
    Button = Button

    def __init__(self, config: Config):
        super().__init__()

        # Initialize Pygame
        pygame.init()

        self.config = config

        self.initialize_buttons()
        self.initialize_sticks()
        self.multi_button_events = MultiButtonEvents()

        self.pygame_controller = None

        # State
        self.multi_button_event_timer: threading.Timer | None = None
        """Timer is used to fire the multi button event after a certain time without any new button press"""
        self.is_multi_buttons_pressed = False
        """Is True after a down event has been fired as long as at least one button from a multi button event is still pressed"""
        self.multi_button_event_buttons: list[Button] = []
        """List of buttons that are part of the current multi button event"""
        self.last_multi_button_event_buttons: list[Button] = []
        """List of buttons that were part of the last multi button event, used to identify a double click"""

        # Time tracking
        self.multi_button_pressed_time_start = 0
        """Time when the multi button was last pressed in seconds"""
        self.multi_button_pressed_time_end = 0
        """Time when the multi button was last released in seconds"""
        self.multi_button_last_click_time = 0
        """Time of the release of the last multi button click in seconds"""
        self.multi_button_last_double_click_time = 0
        """Time of the last multi button double click in seconds"""

    def remove_all_event_listeners(self):
        for button in self.buttons.values():
            button.remove_all_event_listeners()
        for stick in self.sticks.values():
            stick.remove_all_event_listeners()
        self.multi_button_events.remove_all_event_listeners()

    def initialize_buttons(self):
        self.buttons: dict[ControllerButtonName, Button] = {}
        for (
            controller_button_name,
            controller_button_index,
        ) in self.config.button_mapping.items():
            button = Button(
                name=controller_button_name,
                index=controller_button_index,
                settings=self.config.settings.controller_settings,
            )
            self.buttons |= {controller_button_name: button}

    def initialize_sticks(self):
        self.sticks: dict[ControllerStickName, Stick] = {}
        for controller_stick_name, (
            axis_x_index,
            axis_y_index,
        ) in self.config.stick_mapping.items():
            stick = Stick(
                name=controller_stick_name,
                axis_x_index=axis_x_index,
                axis_y_index=axis_y_index,
                settings=self.config.settings.controller_settings,
            )
            self.sticks |= {controller_stick_name: stick}

    def get_buttons_allowed_for_multi_button_event(self) -> list[Button]:
        """Return a list of all buttons that are part of any multi button event."""
        allowed_button_names = []
        for (_, button_names), _ in self.multi_button_events._event_listeners.values():
            for button_name in button_names:
                if button_name not in allowed_button_names:
                    allowed_button_names.append(button_name)
        return [self.buttons[button_name] for button_name in allowed_button_names]

    def get_pressed_multi_buttons(self) -> list[Button]:
        """Return a list of all buttons that are pressed and part of any multi button event."""
        return [
            button
            for button in self.get_buttons_allowed_for_multi_button_event()
            if button.pressed
        ]

    def on_multi_button_down(self):
        """Has to be called when the multi button down event was triggerd."""
        self.is_multi_buttons_pressed = True
        self.multi_button_pressed_time_start = time.time()
        self.multi_button_events.call_event_listeners(
            "down", self.multi_button_event_buttons
        )
        self.multi_button_event_timer = None
        is_same_buttons_as_last_time = set(
            [button.name for button in self.multi_button_event_buttons]
        ) == set([button.name for button in self.last_multi_button_event_buttons])
        if (
            self.multi_button_pressed_time_start
            - self.multi_button_last_double_click_time
            <= self.config.settings.controller_settings.double_click_duration
            and is_same_buttons_as_last_time
        ):
            self.multi_button_events.call_event_listeners(
                "tripple_click", self.last_multi_button_event_buttons
            )
            self.multi_button_last_double_click_time = 0
            self.multi_button_last_click_time = 0
        elif (
            self.multi_button_pressed_time_start - self.multi_button_last_click_time
            <= self.config.settings.controller_settings.double_click_duration
            and is_same_buttons_as_last_time
        ):
            self.multi_button_events.call_event_listeners(
                "double_click", self.last_multi_button_event_buttons
            )
            self.multi_button_last_double_click_time = (
                self.multi_button_pressed_time_start
            )

    def on_multi_button_up(self):
        """Has to be called when the multi button up event was triggerd."""
        self.is_multi_buttons_pressed = False
        self.multi_button_pressed_time_end = time.time()

        self.multi_button_events.call_event_listeners(
            "up", self.multi_button_event_buttons
        )
        self.last_multi_button_event_buttons = self.multi_button_event_buttons

        press_duration = (
            self.multi_button_pressed_time_end - self.multi_button_pressed_time_start
        )

        if (
            press_duration
            > self.config.settings.controller_settings.single_click_duration
        ):
            self.multi_button_events.call_event_listeners(
                "long_press", self.multi_button_event_buttons
            )
        else:
            self.multi_button_events.call_event_listeners(
                "click", self.multi_button_event_buttons
            )
            self.multi_button_last_click_time = self.multi_button_pressed_time_end
        self.multi_button_event_buttons = []

    def handle_multi_button_down(self, button: Button):
        """Has to be called when a button is pressed down."""
        if self.is_multi_buttons_pressed:
            return
        self.multi_button_event_buttons.append(button)
        if self.multi_button_event_timer is not None:
            self.multi_button_event_timer.cancel()
        self.multi_button_event_timer = threading.Timer(
            self.config.settings.controller_settings.multi_click_duration,
            self.on_multi_button_down,
        )
        self.multi_button_event_timer.start()

    def handle_multi_button_up(self, button: Button):
        """Has to be called when a button is released."""
        if any(button.pressed for button in self.multi_button_event_buttons):
            return
        if self.is_multi_buttons_pressed:
            self.on_multi_button_up()
        else:
            # timer has not run out yet, call multi button down events and cancel the timer
            if self.multi_button_event_timer is not None:
                self.multi_button_event_timer.cancel()
                self.multi_button_event_timer = None
            self.on_multi_button_down()
            self.on_multi_button_up()

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
                if button in self.get_buttons_allowed_for_multi_button_event():
                    self.handle_multi_button_down(button)

    def handle_joy_button_up(self, event: pygame.event.Event):
        assert event.type == JOYBUTTONUP
        button_index: int = event.button
        for button in self.buttons.values():
            if button.index == button_index:
                button._up()
                if button in self.get_buttons_allowed_for_multi_button_event():
                    self.handle_multi_button_up(button)

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


if __name__ == "__main__":
    from config import default_config

    controller = Controller(default_config)
    for button in controller.buttons.values():
        for event_type in [
            "down",
            "up",
            "click",
            "long_press",
            "double_click",
            "tripple_click",
        ]:
            button.add_event_listener(
                event_type,
                lambda button, event_type=event_type: print(
                    f"Button {button} {event_type}"
                ),
            )
    for stick in controller.sticks.values():
        stick.add_event_listener(
            "move", lambda stick: print(f"Stick {stick} moved to {stick.x}, {stick.y}")
        )
    for event_type in [
        "down",
        "up",
        "click",
        "long_press",
        "double_click",
        "tripple_click",
    ]:
        controller.multi_button_events.add_event_listener(
            event_type,
            ["shoulder_l", "shoulder_r"],
            lambda buttons, event_type=event_type: print(
                f"Buttons {",".join([button.name for button in buttons])} multi button {event_type}"
            ),
        )
    controller.run()
