import pygame
from pygame.locals import *
from typing import Callable, Optional, List, Tuple, Self
from dataclasses import dataclass
import time

class Button:
    def __init__(self, name: str, index: int, settings: Settings):
        self.name = name
        self.index = index
        self.pressed = False
        self.long_pressed = False

        # internal properties
        self._pressed_time_start = 0  # Time when the button was last pressed in seconds
        self._pressed_time_end = 0  # Time when the button was last released in seconds
        self._last_click_time = 0  # Time of the release of the last click in seconds
        self._last_double_click_time = 0  # Time of the last double click in seconds
        self._settings = settings

        # Event listeners
        self._on_down: List[Callable[[Self], None]] = []
        self._on_up: List[Callable[[Self], None]] = []
        self._on_click: List[Callable[[Self], None]] = []
        self._on_long_press: List[Callable[[Self], None]] = []
        self._on_long_press_start: List[Callable[[Self], None]] = []
        self._on_double_click: List[Callable[[Self], None]] = []
        self._on_tripple_click: List[Callable[[Self], None]] = []

    def on_down(self, listener: Optional[Callable[[Self], None]]):
        """Add a listener for the down event."""
        if listener:
            self._on_down.append(listener)

    def on_up(self, listener: Optional[Callable[[Self], None]]):
        """Add a listener for the up event."""
        if listener:
            self._on_up.append(listener)

    def on_click(self, listener: Optional[Callable[[Self], None]]):
        """Add a listener for the click event."""
        if listener:
            self._on_click.append(listener)

    def on_long_press(self, listener: Optional[Callable[[Self], None]]):
        """Add a listener for the long press event."""
        if listener:
            self._on_long_press.append(listener)

    def on_long_press_start(self, listener: Optional[Callable[[Self], None]]):
        """Add a listener for the long press start event."""
        if listener:
            self._on_long_press_start.append(listener)

    def on_double_click(self, listener: Optional[Callable[[Self], None]]):
        """Add a listener for the double click event."""
        if listener:
            self._on_double_click.append(listener)

    def on_tripple_click(self, listener: Optional[Callable[[Self], None]]):
        """Add a listener for the tripple click event."""
        if listener:
            self._on_tripple_click.append(listener)

    def _down(self):
        """Has to be called when the button is pressed down"""
        self.pressed = True
        self._pressed_time_start = time.time()
        for listener in self._on_down:
            listener(self)

        if (
            self._pressed_time_start - self._last_double_click_time
            <= self._settings.double_click_duration
        ):
            for listener in self._on_tripple_click:
                listener(self)
            self._last_double_click_time = 0
            self._last_click_time = 0
        elif (
            self._pressed_time_start - self._last_click_time
            <= self._settings.double_click_duration
        ):
            for listener in self._on_double_click:
                listener(self)

    def _up(self):
        """Has to be called when the button is released"""
        self.pressed = False
        self.long_pressed = False
        self._pressed_time_end = time.time()

        for listener in self._on_up:
            listener(self)

        press_duration = self._pressed_time_end - self._pressed_time_start

        if press_duration > self._settings.single_click_duration:
            for listener in self._on_long_press:
                listener(self)
        else:
            for listener in self._on_click:
                listener(self)
            self._last_click_time = self._pressed_time_end

    def _update(self):
        """Has to be called every frame"""
        if self.pressed and not self.long_pressed:
            press_duration = time.time() - self._pressed_time_start
            if press_duration > self._settings.single_click_duration:
                self.long_pressed = True
                for listener in self._on_long_press_start:
                    listener(self)

    def __str__(self):
        return self.name


class Joystick(Button):
    def __init__(
        self,
        name: str,
        index: int,
        settings: Settings,
        axis_x_index: int,
        axis_y_index: int,
    ):
        super().__init__(name, index, settings)
        self.axis_x_index = axis_x_index
        self.axis_y_index = axis_y_index
        self.x = 0
        self.y = 0

        # Event listeners
        self._on_move: List[Callable[[Self], None]] = []

    def on_move(self, listener: Optional[Callable[[Self], None]]):
        """Add a listener for the move event."""
        if listener:
            self._on_move.append(listener)

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
        for listener in self._on_move:
            listener(self)

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
        for listener in self._on_move:
            listener(self)


class Controller:
    Joystick = Joystick
    Button = Button
    Settings = Settings

    @dataclass
    class Joysticks:
        left: Joystick
        right: Joystick

    @dataclass
    class Buttons:
        left: Button
        right: Button
        up: Button
        down: Button
        a: Button
        b: Button
        x: Button
        y: Button
        l: Button
        r: Button
        zl: Button
        zr: Button

    def __init__(self, settings: Settings = Settings()):
        # Initialize Pygame
        pygame.init()

        # Define a deadzone value
        self.settings = settings
        self.joystick = self.Joysticks(
            left=Joystick("Left", 12, settings, 0, 1),
            right=Joystick("Right", 13, settings, 2, 3),
        )
        self.button = self.Buttons(
            left=Button("Left", -1, settings),
            right=Button("Right", -1, settings),
            up=Button("Up", -1, settings),
            down=Button("Down", -1, settings),
            b=Button("B", 0, settings),
            a=Button("A", 1, settings),
            x=Button("X", 2, settings),
            y=Button("Y", 3, settings),
            l=Button("L", 5, settings),
            r=Button("R", 6, settings),
            zl=Button("ZL", 7, settings),
            zr=Button("ZR", 8, settings),
        )
        self.pygame_controller = None

    def on_joy_disconnect(self):
        print("Controller disconnected")
        self.pygame_controller = None

    def on_joy_connect(self):
        if not self.pygame_controller:
            self.pygame_controller = self.get_connected_controller()
            if self.pygame_controller:
                print(f"controller connected: {self.pygame_controller.get_name()}")

    def run(self) -> None:
        # Initialize the controller
        pygame.joystick.init()
        self.on_joy_connect()

        self.last_joy_connection_check = time.time()
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == JOYAXISMOTION:
                    if event.axis == self.joystick.left.axis_x_index:
                        self.joystick.left._move_x(event.value)
                    elif event.axis == self.joystick.left.axis_y_index:
                        self.joystick.left._move_y(event.value)
                    elif event.axis == self.joystick.right.axis_x_index:
                        self.joystick.right._move_x(event.value)
                    elif event.axis == self.joystick.right.axis_y_index:
                        self.joystick.right._move_y(event.value)
                elif event.type == JOYBUTTONDOWN:
                    if event.button == self.button.a.index:
                        self.button.a._down()
                    elif event.button == self.button.b.index:
                        self.button.b._down()
                    elif event.button == self.button.x.index:
                        self.button.x._down()
                    elif event.button == self.button.y.index:
                        self.button.y._down()
                    elif event.button == self.button.l.index:
                        self.button.l._down()
                    elif event.button == self.button.r.index:
                        self.button.r._down()
                    elif event.button == self.button.zl.index:
                        self.button.zl._down()
                    elif event.button == self.button.zr.index:
                        self.button.zr._down()
                    elif event.button == self.joystick.left.index:
                        self.joystick.left._down()
                    elif event.button == self.joystick.right.index:
                        self.joystick.right._down()
                elif event.type == JOYBUTTONUP:
                    if event.button == self.button.left.index:
                        self.button.left._up()
                    elif event.button == self.button.right.index:
                        self.button.right._up()
                    elif event.button == self.button.up.index:
                        self.button.up._up()
                    elif event.button == self.button.down.index:
                        self.button.down._up()
                    elif event.button == self.button.a.index:
                        self.button.a._up()
                    elif event.button == self.button.b.index:
                        self.button.b._up()
                    elif event.button == self.button.x.index:
                        self.button.x._up()
                    elif event.button == self.button.y.index:
                        self.button.y._up()
                    elif event.button == self.button.l.index:
                        self.button.l._up()
                    elif event.button == self.button.r.index:
                        self.button.r._up()
                    elif event.button == self.button.zl.index:
                        self.button.zl._up()
                    elif event.button == self.button.zr.index:
                        self.button.zr._up()
                    elif event.button == self.joystick.left.index:
                        self.joystick.left._up()
                    elif event.button == self.joystick.right.index:
                        self.joystick.right._up()
                elif event.type == JOYHATMOTION:
                    if event.value[0] == -1 and not self.button.left.pressed:
                        self.button.left._down()
                    if event.value[0] == 1 and not self.button.right.pressed:
                        self.button.right._down()
                    if event.value[1] == 1 and not self.button.up.pressed:
                        self.button.up._down()
                    if event.value[1] == -1 and not self.button.down.pressed:
                        self.button.down._down()
                    if event.value[0] == 0 and self.button.left.pressed:
                        self.button.left._up()
                    if event.value[0] == 0 and self.button.right.pressed:
                        self.button.right._up()
                    if event.value[1] == 0 and self.button.up.pressed:
                        self.button.up._up()
                    if event.value[1] == 0 and self.button.down.pressed:
                        self.button.down._up()
                elif event.type == JOYDEVICEREMOVED:
                    self.on_joy_disconnect()
                elif event.type == JOYDEVICEADDED:
                    self.on_joy_connect()
            if (
                not self.pygame_controller
                and time.time() - self.last_joy_connection_check > 1
            ):
                self.on_joy_connect()
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
    controller = Controller()
    controller.joystick.left.on_move(
        lambda joystick: print(
            f"Joystick {joystick} moved to {joystick.x}, {joystick.y}"
        )
    )
    controller.joystick.right.on_move(
        lambda joystick: print(
            f"Joystick {joystick} moved to {joystick.x}, {joystick.y}"
        )
    )
    controller.button.left.on_down(
        lambda button: print(f"Button {button} pressed down")
    )
    controller.button.left.on_up(lambda button: print(f"Button {button} released"))
    controller.button.left.on_click(lambda button: print(f"Button {button} clicked"))
    controller.button.left.on_long_press(
        lambda button: print(f"Button {button} long pressed")
    )
    controller.button.left.on_long_press_start(
        lambda button: print(f"Button {button} long press started")
    )
    controller.button.left.on_double_click(
        lambda button: print(f"Button {button} double click")
    )
    controller.joystick.left.on_down(
        lambda joystick: print(f"Joystick {joystick} pressed down")
    )
    # controller.gestures.on_multi_click = lambda buttons: print(
    #     f"Buttons {buttons} clicked at the same time"
    # )  # Called when multiple buttons are pressed at the same time as soon as all buttons are released again

    controller.run()
