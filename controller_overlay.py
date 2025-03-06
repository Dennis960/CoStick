from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPolygonF
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent, QPaintEvent, QImage
from controller import Controller, ControllerButtonName


button_pressed_color = Qt.GlobalColor.gray
button_default_color = Qt.GlobalColor.white
button_highlight_color = Qt.GlobalColor.yellow


class ButtonWidget(QWidget):
    pressed = False
    highlighted = False
    name: ControllerButtonName

    def set_color(self, color):
        self.color = color
        self.update()

    def set_pressed(self, pressed):
        self.pressed = pressed
        self.update()

    def set_highlighted(self, highlighted):
        self.highlighted = highlighted
        self.update()

    def get_button_painter(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.pressed:
            color = button_pressed_color
        elif self.highlighted:
            color = button_highlight_color
        else:
            color = button_default_color
        painter.setBrush(color)
        painter.setPen(color)
        return painter


class JoystickWidget(ButtonWidget):
    def __init__(self, position, diameter, name: ControllerButtonName, parent=None):
        super().__init__(parent)
        self.position = position
        self.diameter = diameter
        self.name = name
        self.color = button_default_color
        self.setGeometry(position[0], position[1], diameter, diameter)

    def move_to(self, x, y):
        """
        Move the joystick relative to its original position to the given x, y coordinates
        """
        scale_factor = 10
        self.move(
            self.position[0] + x * scale_factor, self.position[1] + y * scale_factor
        )

    def paintEvent(self, event: QPaintEvent):
        painter = self.get_button_painter()
        painter.drawEllipse(0, 0, self.diameter, self.diameter)


class FaceButtonWidget(ButtonWidget):
    def __init__(self, position, diameter, name: ControllerButtonName, parent=None):
        super().__init__(parent)
        self.position = position
        self.diameter = diameter
        self.name = name
        self.setGeometry(position[0], position[1], diameter, diameter)

    def paintEvent(self, event: QPaintEvent):
        painter = self.get_button_painter()
        painter.drawEllipse(0, 0, self.diameter, self.diameter)


class DpadButtonWidget(ButtonWidget):
    def __init__(self, position, size, name: ControllerButtonName, parent=None):
        super().__init__(parent)
        self.position = position
        self.size = size
        self.name = name
        self.setGeometry(position[0], position[1], size, size)

    def paintEvent(self, event: QPaintEvent):
        painter = self.get_button_painter()
        painter.drawRect(0, 0, self.size, self.size)


class ShoulderButtonWidget(ButtonWidget):
    def __init__(self, outline, name: ControllerButtonName, parent=None):
        super().__init__(parent)
        self.outline = outline
        max_x = max(x for x, y in outline)
        self.name = name
        max_y = max(y for x, y in outline)
        self.setGeometry(0, 0, max_x, max_y)

    def paintEvent(self, event: QPaintEvent):
        painter = self.get_button_painter()
        painter.drawPolygon(QPolygonF([QPointF(*point) for point in self.outline]))


class ControllerOverlay(QWidget):
    controller_size = (330, 220)
    controller_image = "Controller.png"

    joystick_left_position = (61, 49)
    joystick_right_position = (189, 100)
    joystick_diameter = 38
    dpad_position = (97, 94)
    dpad_arrow_diameter = 17

    button_face_up_position = (241, 34)
    button_face_right_position = (263, 55)
    button_face_down_position = (241, 76)
    button_face_left_position = (219, 55)
    button_diameter = 23

    button_shoulder_left_outline = [(53, 22), (116, 10), (109, 5), (54, 19)]
    button_shoulder_right_outline = [
        (330 - x, y) for x, y in button_shoulder_left_outline
    ]
    button_shoulder_bottom_left_outline = [(56, 17), (106, 3), (101, 0), (56, 15)]
    button_shoulder_bottom_right_outline = [
        (330 - x, y) for x, y in button_shoulder_bottom_left_outline
    ]

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(*self.controller_size)
        self.old_pos = None

        # fmt: off
        self.buttons: dict[ControllerButtonName, ButtonWidget] = {
            "face_up":     FaceButtonWidget(self.button_face_up_position, self.button_diameter, "face_up", self),
            "face_right":  FaceButtonWidget(self.button_face_right_position, self.button_diameter, "face_right", self),
            "face_down":   FaceButtonWidget(self.button_face_down_position, self.button_diameter, "face_down", self),
            "face_left":   FaceButtonWidget(self.button_face_left_position, self.button_diameter, "face_left", self),

            "dpad_up":     DpadButtonWidget((self.dpad_position[0] + self.dpad_arrow_diameter, self.dpad_position[1]), self.dpad_arrow_diameter, "dpad_up", self),
            "dpad_right":  DpadButtonWidget((self.dpad_position[0] + 2 * self.dpad_arrow_diameter, self.dpad_position[1] + self.dpad_arrow_diameter), self.dpad_arrow_diameter, "dpad_right", self),
            "dpad_down":   DpadButtonWidget((self.dpad_position[0] + self.dpad_arrow_diameter, self.dpad_position[1] + 2 * self.dpad_arrow_diameter), self.dpad_arrow_diameter, "dpad_down", self),
            "dpad_left":   DpadButtonWidget((self.dpad_position[0], self.dpad_position[1] + self.dpad_arrow_diameter), self.dpad_arrow_diameter, "dpad_left", self),

            "shoulder_l":  ShoulderButtonWidget(self.button_shoulder_left_outline, "shoulder_l", self),
            "shoulder_r":  ShoulderButtonWidget(self.button_shoulder_right_outline, "shoulder_r", self),
            "shoulder_zl": ShoulderButtonWidget(self.button_shoulder_bottom_left_outline, "shoulder_zl", self),
            "shoulder_zr": ShoulderButtonWidget(self.button_shoulder_bottom_right_outline, "shoulder_zr", self),

            "stick_left":  JoystickWidget(self.joystick_left_position, self.joystick_diameter, "stick_left", self),
            "stick_right": JoystickWidget(self.joystick_right_position, self.joystick_diameter, "stick_right", self),
        }
        self.joystick_left: JoystickWidget = self.buttons["stick_left"]
        self.joystick_right: JoystickWidget = self.buttons["stick_right"]
        # fmt: on

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawImage(0, 0, QImage(self.controller_image))

    def init_controller_event_listeners(self, controller: Controller):
        for button_widget in self.buttons.values():
            controller.buttons[button_widget.name].add_event_listener(
                "down",
                lambda button, button_widget=button_widget: button_widget.set_pressed(
                    True
                ),
            )
            controller.buttons[button_widget.name].add_event_listener(
                "up",
                lambda button, button_widget=button_widget: button_widget.set_pressed(
                    False
                ),
            )

        controller.sticks["stick_left"].add_event_listener(
            "move", lambda joystick: self.joystick_left.move_to(joystick.x, joystick.y)
        )
        controller.sticks["stick_right"].add_event_listener(
            "move", lambda joystick: self.joystick_right.move_to(joystick.x, joystick.y)
        )

    def highlight_buttons(self, button_names: list[ControllerButtonName]):
        """
        Highlight the buttons with the given names and unhighlight
        all other buttons
        """
        for button_widget in self.buttons.values():
            button_widget.set_highlighted(False)
        for button_name in button_names:
            self.buttons[button_name].set_highlighted(True)


class Trainer:
    """
    The trainer is a helper class to highlight buttons that should be pressed next and
    unhighlight them when they are pressed
    """

    def __init__(self, controller_overlay: ControllerOverlay):
        self.controller_overlay = controller_overlay

    def highlight_buttons(self, button_names: list[ControllerButtonName]):
        self.controller_overlay.highlight_buttons(button_names)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from controller import Controller
    from config import Config
    import threading

    app = QApplication(sys.argv)
    window = ControllerOverlay()
    window.show()

    config = Config.load_config()
    controller = Controller(config)

    window.init_controller_event_listeners(controller)

    # Debug
    button_names: list[ControllerButtonName] = [
        "face_right",
        "shoulder_l",
    ]
    window.highlight_buttons(button_names)

    listener_id = controller.multi_button_events.add_event_listener(
        "down",
        button_names,
        lambda buttons: (
            print("Down"),
            window.highlight_buttons([]),
            controller.multi_button_events.remove_event_listener(listener_id),
        ),
    )
    # Debug end

    controller_thread = threading.Thread(target=controller.run)
    controller_thread.start()

    app.exec()
    controller.running = False
    controller_thread.join()
