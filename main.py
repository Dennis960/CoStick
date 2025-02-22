import sys
from typing import Literal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from controller import Controller
import threading
import time

from controller_overlay import ControllerOverlay
from config import *
import pyautogui

# Remove pyautogui delays
pyautogui.PAUSE = 0
# Remove pyautogui failsafes
pyautogui.FAILSAFE = False


class Cursor:
    mode: Mode

    def __init__(
        self, window: ControllerOverlay, controller: Controller, config: Config
    ):
        self.window = window
        self.controller = controller
        self.config = config
        self.last_time = time.time()
        self.boost = False
        self.boost_start_time = None
        self.target_scroll = 0
        self.setup()

    def execute_action(self, action: ComputerAction | SwitchModeAction):
        if action.action == "switch_mode":
            self.toggle_mode(action.mode)
        elif action.action == "key_down":
            pyautogui.keyDown(action.key)
        elif action.action == "key_up":
            pyautogui.keyUp(action.key)
        elif action.action == "mouse_down":
            pyautogui.mouseDown(button=action.button)
        elif action.action == "mouse_up":
            pyautogui.mouseUp(button=action.button)
        elif action.action == "type":
            pyautogui.typewrite(action.text)
        elif action.action == "key_press":
            pyautogui.press(action.key)
        else:
            print(f"Action {action.action} not found")

    def add_button_action_listeners(
        self,
        controller_button_name: ControllerButtonName,
        controller_button_event_name: ControllerButtonEventName,
        actions: list[ComputerAction | SwitchModeAction],
    ):
        # Find the button on the controller
        button = self.controller.buttons.get(controller_button_name, None)
        if button is None:
            print(f"Button {controller_button_name} not found")
            return

        # Add the listeners
        for action in actions:
            button.add_event_listener(
                controller_button_event_name,
                lambda button, action=action: self.execute_action(action),
            )

    def add_stick_action_listeners(
        self,
        controller_stick_name: ControllerStickName,
        controller_stick_event_name: ControllerStickEventName,
        actions: list[ComputerNavigationAction, SwitchModeAction],
    ):
        stick = self.controller.sticks.get(controller_stick_name, None)
        if stick is None:
            print(f"Stick {controller_stick_name} not found")
            return

        for action in actions:
            if action.action == "switch_mode":
                stick.add_event_listener(
                    controller_stick_event_name,
                    lambda stick, action=action: self.toggle_mode(action.mode),
                )
            elif action.action == "mouse_move":
                pass
            elif action.action == "scroll":
                pass
            else:
                print(f"Action {action.action} not found")

    def on_multi_button_event(
        self,
        actions: list[ComputerAction | SwitchModeAction],
    ):
        for action in actions:
            self.execute_action(action)

    def toggle_mode(self, mode_name: str):
        print(f"Switching to mode {mode_name}")
        self.controller.remove_all_event_listeners()
        self.window.init_controller_event_listeners(
            self.controller
        )  # TODO make this better by not removing the listeners in the first place

        self.mode = config.modes.get(mode_name, None)
        if self.mode is None:
            print(f"Mode {self.mode} not found. Falling back to default mode")
            self.mode = config.modes["default"]
        # insert all actions from global mode which are not defined in the current mode
        global_mode = config.modes["global"]
        if self.mode.button_actions is None:
            self.mode.button_actions = {}
        if self.mode.stick_actions is None:
            self.mode.stick_actions = {}
        if self.mode.multi_button_actions is None:
            self.mode.multi_button_actions = []
        if global_mode.button_actions is not None:
            for (
                controller_button_name,
                action_details,
            ) in global_mode.button_actions.items():
                if controller_button_name not in self.mode.button_actions:
                    self.mode.button_actions[controller_button_name] = action_details
        if global_mode.stick_actions is not None:
            for (
                controller_stick_name,
                action_details,
            ) in global_mode.stick_actions.items():
                if controller_stick_name not in self.mode.stick_actions:
                    self.mode.stick_actions[controller_stick_name] = action_details

        for controller_button_name, action_details in self.mode.button_actions.items():
            for controller_button_event_name, actions in action_details.items():
                if not isinstance(actions, list):
                    actions = [actions]
                self.add_button_action_listeners(
                    controller_button_name, controller_button_event_name, actions
                )

        for controller_stick_name, action_details in self.mode.stick_actions.items():
            for controller_stick_event_name, actions in action_details.items():
                if not isinstance(actions, list):
                    actions = [actions]
                self.add_stick_action_listeners(
                    controller_stick_name, controller_stick_event_name, actions
                )

        for multi_button_action in self.mode.multi_button_actions:
            for (
                controller_button_event_name,
                actions,
            ) in multi_button_action.actions.items():
                if not isinstance(actions, list):
                    actions = [actions]
                self.controller.add_multi_button_event_listener(
                    controller_button_event_name,
                    multi_button_action.buttons,
                    lambda buttons, actions=actions: self.on_multi_button_event(
                        actions
                    ),
                )

    def setup(self):
        self.toggle_mode("default")

    def on_update_stick_move_event(
        self,
        delta_time: float,
        controller_stick_name: ControllerStickName,
        action: ComputerNavigationAction,
    ):
        stick = self.controller.sticks.get(controller_stick_name, None)
        if stick is None:
            print(f"Stick {controller_stick_name} not found")
            return

        if action.action == "mouse_move":
            self.move_cursor(stick.x, stick.y, delta_time)
        elif action.action == "scroll":
            self.scroll(stick.y, stick.x, delta_time)
        else:
            print(f"Action {action.action} not found")

    def update(self):
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time

        for controller_stick_name, action_details in self.mode.stick_actions.items():
            for controller_stick_event_name, actions in action_details.items():
                if not isinstance(actions, list):
                    actions = [actions]
                for action in [
                    actions for actions in actions if actions.action != "switch_mode"
                ]:
                    if controller_stick_event_name == "move":
                        self.on_update_stick_move_event(
                            delta_time,
                            controller_stick_name,
                            action,
                        )
                    else:
                        print(f"Event {controller_stick_event_name} not found")

    def move_cursor(self, x_value, y_value, delta_time):
        speed = pow(pow(x_value, 2) + pow(y_value, 2), 0.5)  # Between 0 and 1
        is_boosting = False
        if speed > 0.95:
            speed = 1
            if not self.boost:
                self.boost = True
                self.boost_start_time = time.time()
            elif (
                time.time() - self.boost_start_time
                >= self.config.settings.cursor_settings.cursor_boost_acceleration_delay
            ):
                is_boosting = True
        else:
            self.boost = False
        if is_boosting:
            boost_time = (
                time.time()
                - self.boost_start_time
                - self.config.settings.cursor_settings.cursor_boost_acceleration_delay
            )
            boost_factor = (
                boost_time
                / self.config.settings.cursor_settings.cursor_boost_acceleration_time
            )  # Between 0 and 1
            if boost_factor > 1:
                boost_factor = 1
            if boost_factor < 0:
                boost_factor = 0
            speed = (
                1
                + boost_factor * self.config.settings.cursor_settings.cursor_boost_speed
            )
        elif speed < 0.05:
            speed = 0
        else:
            speed = 1.5 * pow(2.4, 4.3 * (speed - 1.1))  # ~ Between 0 and 1

        x_value *= speed
        y_value *= speed
        distance_x = (
            x_value
            * self.config.settings.cursor_settings.cursor_speed_pixels_per_second
            * delta_time
        )
        distance_y = (
            y_value
            * self.config.settings.cursor_settings.cursor_speed_pixels_per_second
            * delta_time
        )
        pyautogui.moveRel(distance_x, distance_y)

    def scroll(self, y_value, x_value, delta_time):
        if (y_value > 0) != (self.target_scroll > 0):
            self.target_scroll = 0
        self.target_scroll += (
            y_value * self.config.settings.cursor_settings.scroll_speed
        )
        if abs(self.target_scroll) >= 1:
            scroll_amount = int(self.target_scroll)
            self.target_scroll -= scroll_amount
            pyautogui.scroll(-scroll_amount)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControllerOverlay()
    config = Config.load_config()
    window.show()

    controller = Controller(config)

    window.init_controller_event_listeners(controller)

    controller_thread = threading.Thread(target=controller.run)
    controller_thread.start()

    update_manager = Cursor(window, controller, config)

    timer = QTimer()
    timer.setTimerType(Qt.TimerType.PreciseTimer)
    timer.timeout.connect(update_manager.update)
    timer.start(16)  # Approximately 60 FPS

    app.exec()
    controller.running = False
    controller_thread.join()
