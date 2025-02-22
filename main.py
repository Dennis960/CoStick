import sys
from typing import Literal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from controller import Controller
import threading
import time

from controller_overlay import XboxControllerOverlay
import pyautogui

CURSOR_SPEED_PIXELS_PER_SECOND = 800
CURSOR_BOOST_SPEED = 5
CURSOR_BOOST_ACCELERATION_DELAY = 0.2  # Cursor will wait for this time before boosting
CURSOR_BOOST_ACCELERATION_TIME = (
    0.5  # Cursor will take this time to reach the boost speed
)
SCROLL_SPEED = 0.5

# Remove pyautogui delays
pyautogui.PAUSE = 0


class Cursor:
    def __init__(self, window: XboxControllerOverlay, controller: Controller):
        self.window = window
        self.controller = controller
        self.last_time = time.time()
        self.boost = False
        self.boost_start_time = None
        self.target_scroll = 0
        self.mode: Literal["mouse", "selection"] = "mouse"
        self.setup()

    def setup(self):
        def on_button_down(button: Controller.Button):
            if button == Controller.Button.A:
                pyautogui.mouseDown() if self.mode == "mouse" else pyautogui.keyDown("shift")
            elif button == Controller.Button.B:
                pyautogui.mouseDown(button="right") if self.mode == "mouse" else pyautogui.keyDown("ctrl")
            elif button == Controller.Button.UP:
                pyautogui.keyDown("up")
            elif button == Controller.Button.DOWN:
                pyautogui.keyDown("down")
            elif button == Controller.Button.LEFT:
                pyautogui.keyDown("left")
            elif button == Controller.Button.RIGHT:
                pyautogui.keyDown("right")
        self.controller.button.on_down()
        self.controller.button.a.on_down(lambda button: pyautogui.mouseDown() if self.mode == "mouse" else pyautogui.keyDown("shift"))
        self.controller.button.a.on_up(lambda button: pyautogui.mouseUp() if self.mode == "mouse" else pyautogui.keyUp("shift"))
        self.controller.button.b.on_down(lambda button: pyautogui.mouseDown(button="right") if self.mode == "mouse" else pyautogui.keyDown("ctrl"))
        self.controller.button.b.on_up(lambda button: pyautogui.mouseUp(button="right") if self.mode == "mouse" else pyautogui.keyUp("ctrl"))

        self.controller.button.up.on_down(lambda button: pyautogui.keyDown("up"))
        self.controller.button.up.on_up(lambda button: pyautogui.keyUp("up"))
        self.controller.button.down.on_down(lambda button: pyautogui.keyDown("down"))
        self.controller.button.down.on_up(lambda button: pyautogui.keyUp("down"))
        self.controller.button.left.on_down(lambda button: pyautogui.keyDown("left"))
        self.controller.button.left.on_up(lambda button: pyautogui.keyUp("left"))
        self.controller.button.right.on_down(lambda button: pyautogui.keyDown("right"))
        self.controller.button.right.on_up(lambda button: pyautogui.keyUp("right"))

        def on_move(joystick):
            self.mode = "mouse"

        self.controller.joystick.left.on_move(on_move)
        self.controller.joystick.right.on_move(on_move)

        def on_dpad(button):
            self.mode = "selection"
        
        self.controller.button.up.on_down(on_dpad)
        self.controller.button.down.on_down(on_dpad)
        self.controller.button.left.on_down(on_dpad)
        self.controller.button.right.on_down(on_dpad)

    def update(self):
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        self.move_cursor(
            self.controller.joystick.left.x, self.controller.joystick.left.y, delta_time
        )
        self.scroll(
            self.controller.joystick.right.y,
            self.controller.joystick.right.x,
            delta_time,
        )

    def move_cursor(self, x_value, y_value, delta_time):
        speed = pow(pow(x_value, 2) + pow(y_value, 2), 0.5)  # Between 0 and 1
        is_boosting = False
        if speed > 0.95:
            speed = 1
            if not self.boost:
                self.boost = True
                self.boost_start_time = time.time()
            elif time.time() - self.boost_start_time >= CURSOR_BOOST_ACCELERATION_DELAY:
                is_boosting = True
        else:
            self.boost = False
        if is_boosting:
            boost_time = (
                time.time() - self.boost_start_time - CURSOR_BOOST_ACCELERATION_DELAY
            )
            boost_factor = (
                boost_time / CURSOR_BOOST_ACCELERATION_TIME
            )  # Between 0 and 1
            if boost_factor > 1:
                boost_factor = 1
            if boost_factor < 0:
                boost_factor = 0
            speed = 1 + boost_factor * CURSOR_BOOST_SPEED
        elif speed < 0.05:
            speed = 0
        else:
            speed = 1.5 * pow(2.4, 4.3 * (speed - 1.1))  # ~ Between 0 and 1

        x_value *= speed
        y_value *= speed
        distance_x = x_value * CURSOR_SPEED_PIXELS_PER_SECOND * delta_time
        distance_y = y_value * CURSOR_SPEED_PIXELS_PER_SECOND * delta_time
        pyautogui.moveRel(distance_x, distance_y)

    def scroll(self, y_value, x_value, delta_time):
        if (y_value > 0) != (self.target_scroll > 0):
            self.target_scroll = 0
        self.target_scroll += y_value * SCROLL_SPEED
        if abs(self.target_scroll) >= 1:
            scroll_amount = int(self.target_scroll)
            self.target_scroll -= scroll_amount
            pyautogui.scroll(-scroll_amount)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = XboxControllerOverlay()
    window.show()

    controller = Controller()

    window.init_controller(controller)

    controller_thread = threading.Thread(target=controller.run)
    controller_thread.start()

    update_manager = Cursor(window, controller)

    timer = QTimer()
    timer.setTimerType(Qt.TimerType.PreciseTimer)
    timer.timeout.connect(update_manager.update)
    timer.start(16)  # Approximately 60 FPS

    app.exec()
    controller.running = False
    controller_thread.join()
