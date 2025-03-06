from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QPolygonF
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent, QPaintEvent, QImage
from controller import Controller


button_pressed_color = Qt.GlobalColor.gray
button_default_color = Qt.GlobalColor.white


class ButtonWidget(QWidget):
    color = button_default_color

    def set_pressed(self, pressed):
        self.color = button_pressed_color if pressed else button_default_color
        self.update()

    def get_button_painter(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(self.color)
        return painter


class JoystickWidget(ButtonWidget):
    def __init__(self, position, diameter, parent=None):
        super().__init__(parent)
        self.position = position
        self.diameter = diameter
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
    def __init__(self, position, diameter, label, parent=None):
        super().__init__(parent)
        self.position = position
        self.diameter = diameter
        self.label = label
        self.pressed = False
        self.setGeometry(position[0], position[1], diameter, diameter)

    def paintEvent(self, event: QPaintEvent):
        painter = self.get_button_painter()
        painter.drawEllipse(0, 0, self.diameter, self.diameter)
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.drawText(self.diameter / 2 - 4, self.diameter / 2 + 5, self.label)


class DpadButtonWidget(ButtonWidget):
    def __init__(self, position, size, direction, parent=None):
        super().__init__(parent)
        self.position = position
        self.size = size
        self.direction = direction
        self.setGeometry(position[0], position[1], size, size)

    def paintEvent(self, event: QPaintEvent):
        painter = self.get_button_painter()
        painter.drawRect(0, 0, self.size, self.size)


class ShoulderButtonWidget(ButtonWidget):
    def __init__(self, outline, parent=None):
        super().__init__(parent)
        self.outline = outline
        max_x = max(x for x, y in outline)
        max_y = max(y for x, y in outline)
        self.setGeometry(0, 0, max_x, max_y)

    def paintEvent(self, event: QPaintEvent):
        painter = self.get_button_painter()
        painter.drawPolygon(QPolygonF([QPointF(*point) for point in self.outline]))


class ControllerOverlay(QWidget):
    controller_size = (330, 220)
    controller_image = "Controller.png"

    left_joystick_position = (61, 49)
    right_joystick_position = (189, 100)
    joystick_diameter = 38
    dpad_position = (97, 94)
    dpad_arrow_diameter = 17

    button_left_position = (219, 55)
    button_top_position = (241, 34)
    button_right_position = (263, 55)
    button_bottom_position = (241, 76)
    button_diameter = 23

    left_shoulder_button_outline = [(53, 22), (116, 10), (109, 5), (54, 19)]
    right_shoulder_button_outline = [
        (330 - x, y) for x, y in left_shoulder_button_outline
    ]
    bottom_left_shoulder_button_outline = [(56, 17), (106, 3), (101, 0), (56, 15)]
    bottom_right_shoulder_button_outline = [
        (330 - x, y) for x, y in bottom_left_shoulder_button_outline
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
        self.left_joystick = JoystickWidget(self.left_joystick_position, self.joystick_diameter, self)
        self.right_joystick = JoystickWidget(self.right_joystick_position, self.joystick_diameter, self)

        self.button_a = FaceButtonWidget(self.button_right_position, self.button_diameter, "A", self)
        self.button_b = FaceButtonWidget(self.button_bottom_position, self.button_diameter, "B", self)
        self.button_x = FaceButtonWidget(self.button_top_position, self.button_diameter, "X", self)
        self.button_y = FaceButtonWidget(self.button_left_position, self.button_diameter, "Y", self)

        self.dpad_left = DpadButtonWidget((self.dpad_position[0], self.dpad_position[1] + self.dpad_arrow_diameter), self.dpad_arrow_diameter, "left", self)
        self.dpad_down = DpadButtonWidget((self.dpad_position[0] + self.dpad_arrow_diameter, self.dpad_position[1] + 2 * self.dpad_arrow_diameter), self.dpad_arrow_diameter, "down", self)
        self.dpad_right = DpadButtonWidget((self.dpad_position[0] + 2 * self.dpad_arrow_diameter, self.dpad_position[1] + self.dpad_arrow_diameter), self.dpad_arrow_diameter, "right", self)
        self.dpad_up = DpadButtonWidget((self.dpad_position[0] + self.dpad_arrow_diameter, self.dpad_position[1]), self.dpad_arrow_diameter, "up", self)

        self.left_shoulder_button = ShoulderButtonWidget(self.left_shoulder_button_outline, self)
        self.right_shoulder_button = ShoulderButtonWidget(self.right_shoulder_button_outline, self)
        self.bottom_left_shoulder_button = ShoulderButtonWidget(self.bottom_left_shoulder_button_outline, self)
        self.bottom_right_shoulder_button = ShoulderButtonWidget(self.bottom_right_shoulder_button_outline, self)
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
        # fmt: off
        controller.buttons["face_right"].add_event_listener("down", lambda button: self.button_a.set_pressed(button.pressed))
        controller.buttons["face_right"].add_event_listener("up", lambda button: self.button_a.set_pressed(button.pressed))
        controller.buttons["face_down"].add_event_listener("down", lambda button: self.button_b.set_pressed(button.pressed))
        controller.buttons["face_down"].add_event_listener("up", lambda button: self.button_b.set_pressed(button.pressed))
        controller.buttons["face_up"].add_event_listener("down", lambda button: self.button_x.set_pressed(button.pressed))
        controller.buttons["face_up"].add_event_listener("up", lambda button: self.button_x.set_pressed(button.pressed))
        controller.buttons["face_left"].add_event_listener("down", lambda button: self.button_y.set_pressed(button.pressed))
        controller.buttons["face_left"].add_event_listener("up", lambda button: self.button_y.set_pressed(button.pressed))
        controller.buttons["dpad_left"].add_event_listener("down", lambda button: self.dpad_left.set_pressed(button.pressed))
        controller.buttons["dpad_left"].add_event_listener("up", lambda button: self.dpad_left.set_pressed(button.pressed))
        controller.buttons["dpad_down"].add_event_listener("down", lambda button: self.dpad_down.set_pressed(button.pressed))
        controller.buttons["dpad_down"].add_event_listener("up", lambda button: self.dpad_down.set_pressed(button.pressed))
        controller.buttons["dpad_right"].add_event_listener("down", lambda button: self.dpad_right.set_pressed(button.pressed))
        controller.buttons["dpad_right"].add_event_listener("up", lambda button: self.dpad_right.set_pressed(button.pressed))
        controller.buttons["dpad_up"].add_event_listener("down", lambda button: self.dpad_up.set_pressed(button.pressed))
        controller.buttons["dpad_up"].add_event_listener("up", lambda button: self.dpad_up.set_pressed(button.pressed))
        controller.buttons["shoulder_l"].add_event_listener("down", lambda button: self.left_shoulder_button.set_pressed(button.pressed))
        controller.buttons["shoulder_l"].add_event_listener("up", lambda button: self.left_shoulder_button.set_pressed(button.pressed))
        controller.buttons["shoulder_r"].add_event_listener("down", lambda button: self.right_shoulder_button.set_pressed(button.pressed))
        controller.buttons["shoulder_r"].add_event_listener("up", lambda button: self.right_shoulder_button.set_pressed(button.pressed))
        controller.buttons["shoulder_zl"].add_event_listener("down", lambda button: self.bottom_left_shoulder_button.set_pressed(button.pressed))
        controller.buttons["shoulder_zl"].add_event_listener("up", lambda button: self.bottom_left_shoulder_button.set_pressed(button.pressed))
        controller.buttons["shoulder_zr"].add_event_listener("down", lambda button: self.bottom_right_shoulder_button.set_pressed(button.pressed))
        controller.buttons["shoulder_zr"].add_event_listener("up", lambda button: self.bottom_right_shoulder_button.set_pressed(button.pressed))
        controller.buttons["stick_left"].add_event_listener("down", lambda button: self.left_joystick.set_pressed(button.pressed))
        controller.buttons["stick_left"].add_event_listener("up", lambda button: self.left_joystick.set_pressed(button.pressed))
        controller.buttons["stick_right"].add_event_listener("down", lambda button: self.right_joystick.set_pressed(button.pressed))
        controller.buttons["stick_right"].add_event_listener("up", lambda button: self.right_joystick.set_pressed(button.pressed))


        controller.sticks["stick_left"].add_event_listener("move", lambda joystick: self.left_joystick.move_to(joystick.x, joystick.y))
        controller.sticks["stick_right"].add_event_listener("move", lambda joystick: self.right_joystick.move_to(joystick.x, joystick.y))
        # fmt: on


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

    controller_thread = threading.Thread(target=controller.run)
    controller_thread.start()

    app.exec()
    controller.running = False
    controller_thread.join()
