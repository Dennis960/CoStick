import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from controller import Controller
import threading
import time
import math

from controller_overlay import XboxControllerOverlay
import pyautogui

CURSOR_SPEED_PIXELS_PER_SECOND = 800
CURSOR_BOOST_SPEED = 3
CURSOR_BOOST_ACCELERATION_DELAY = 0.2  # Cursor will wait for this time before boosting
CURSOR_BOOST_ACCELERATION_TIME = (
    0.5  # Cursor will take this time to reach the boost speed
)

# Remove pyautogui delays
pyautogui.PAUSE = 0


class Cursor:
    def __init__(self, window: XboxControllerOverlay, controller: Controller):
        self.window = window
        self.controller = controller
        self.last_time = time.time()
        self.boost = False
        self.boost_start_time = None
        self.setup()

    def setup(self):
        self.controller.button.a.on_down(lambda button: pyautogui.mouseDown())
        self.controller.button.a.on_up(lambda button: pyautogui.mouseUp())
        self.controller.button.a.on_down(lambda button: print("down"))
        self.controller.button.a.on_up(lambda button: print("up"))

    def update(self):
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        x_value = self.controller.joystick.left.x
        y_value = self.controller.joystick.left.y
        self.move_cursor(x_value, y_value, delta_time)

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
