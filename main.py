import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPainter, QPen, QPolygonF
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent, QPaintEvent
from controller import Controller
import threading


class JoystickWidget(QWidget):
    def __init__(self, position, diameter, parent=None):
        super().__init__(parent)
        self.position = position
        self.diameter = diameter
        self.setGeometry(position[0], position[1], diameter, diameter)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(0, 0, self.diameter, self.diameter)


class FaceButtonWidget(QWidget):
    def __init__(self, position, diameter, label, parent=None):
        super().__init__(parent)
        self.position = position
        self.diameter = diameter
        self.label = label
        self.pressed = False
        self.setGeometry(position[0], position[1], diameter, diameter)

    def toggle_pressed(self):
        self.pressed = not self.pressed
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.gray if self.pressed else Qt.GlobalColor.white)
        painter.drawEllipse(0, 0, self.diameter, self.diameter)
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.drawText(self.diameter / 2 - 4, self.diameter / 2 + 5, self.label)


class DpadButtonWidget(QWidget):
    def __init__(self, position, size, direction, parent=None):
        super().__init__(parent)
        self.position = position
        self.size = size
        self.direction = direction
        self.pressed = False
        self.setGeometry(position[0], position[1], size, size)

    def toggle_pressed(self):
        self.pressed = not self.pressed
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.gray if self.pressed else Qt.GlobalColor.white)
        painter.drawRect(0, 0, self.size, self.size)


class ShoulderButtonWidget(QWidget):
    def __init__(self, outline, parent=None):
        super().__init__(parent)
        self.outline = outline
        self.pressed = False
        self.setGeometry(0, 0, 330, 215)  # Assuming the size of the controller

    def toggle_pressed(self):
        self.pressed = not self.pressed
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.gray if self.pressed else Qt.GlobalColor.white)
        painter.drawPolygon(QPolygonF([QPointF(*point) for point in self.outline]))


class XboxControllerOverlay(QWidget):
    controller_size = (330, 215)
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

        self.left_joystick = JoystickWidget(
            self.left_joystick_position, self.joystick_diameter, self
        )
        self.right_joystick = JoystickWidget(
            self.right_joystick_position, self.joystick_diameter, self
        )

        self.button_a = FaceButtonWidget(
            self.button_right_position, self.button_diameter, "A", self
        )
        self.button_b = FaceButtonWidget(
            self.button_bottom_position, self.button_diameter, "B", self
        )
        self.button_x = FaceButtonWidget(
            self.button_top_position, self.button_diameter, "X", self
        )
        self.button_y = FaceButtonWidget(
            self.button_left_position, self.button_diameter, "Y", self
        )

        self.dpad_left = DpadButtonWidget(
            (self.dpad_position[0], self.dpad_position[1] + self.dpad_arrow_diameter),
            self.dpad_arrow_diameter,
            "left",
            self,
        )
        self.dpad_down = DpadButtonWidget(
            (
                self.dpad_position[0] + self.dpad_arrow_diameter,
                self.dpad_position[1] + 2 * self.dpad_arrow_diameter,
            ),
            self.dpad_arrow_diameter,
            "down",
            self,
        )
        self.dpad_right = DpadButtonWidget(
            (
                self.dpad_position[0] + 2 * self.dpad_arrow_diameter,
                self.dpad_position[1] + self.dpad_arrow_diameter,
            ),
            self.dpad_arrow_diameter,
            "right",
            self,
        )
        self.dpad_up = DpadButtonWidget(
            (self.dpad_position[0] + self.dpad_arrow_diameter, self.dpad_position[1]),
            self.dpad_arrow_diameter,
            "up",
            self,
        )

        self.left_shoulder_button = ShoulderButtonWidget(
            self.left_shoulder_button_outline, self
        )
        self.right_shoulder_button = ShoulderButtonWidget(
            self.right_shoulder_button_outline, self
        )
        self.bottom_left_shoulder_button = ShoulderButtonWidget(
            self.bottom_left_shoulder_button_outline, self
        )
        self.bottom_right_shoulder_button = ShoulderButtonWidget(
            self.bottom_right_shoulder_button_outline, self
        )

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

        # Draw controller body from image
        # painter.drawImage(0, 0, self.controller_image) # TODO fix


if __name__ == "__main__":
    controller = Controller()

    # fmt: off
    controller.button.a.on_down(lambda _: window.button_a.toggle_pressed())
    controller.button.a.on_up(lambda _: window.button_a.toggle_pressed())
    controller.button.b.on_down(lambda _: window.button_b.toggle_pressed())
    controller.button.b.on_up(lambda _: window.button_b.toggle_pressed())
    controller.button.x.on_down(lambda _: window.button_x.toggle_pressed())
    controller.button.x.on_up(lambda _: window.button_x.toggle_pressed())
    controller.button.y.on_down(lambda _: window.button_y.toggle_pressed())
    controller.button.y.on_up(lambda _: window.button_y.toggle_pressed())
    controller.button.left.on_down(lambda _: window.dpad_left.toggle_pressed())
    controller.button.left.on_up(lambda _: window.dpad_left.toggle_pressed())
    controller.button.down.on_down(lambda _: window.dpad_down.toggle_pressed())
    controller.button.down.on_up(lambda _: window.dpad_down.toggle_pressed())
    controller.button.right.on_down(lambda _: window.dpad_right.toggle_pressed())
    controller.button.right.on_up(lambda _: window.dpad_right.toggle_pressed())
    controller.button.up.on_down(lambda _: window.dpad_up.toggle_pressed())
    controller.button.up.on_up(lambda _: window.dpad_up.toggle_pressed())
    controller.button.l.on_down(lambda _: window.left_shoulder_button.toggle_pressed())
    controller.button.l.on_up(lambda _: window.left_shoulder_button.toggle_pressed())
    controller.button.r.on_down(lambda _: window.right_shoulder_button.toggle_pressed())
    controller.button.r.on_up(lambda _: window.right_shoulder_button.toggle_pressed())
    controller.button.zl.on_down(lambda _: window.bottom_left_shoulder_button.toggle_pressed())
    controller.button.zl.on_up(lambda _: window.bottom_left_shoulder_button.toggle_pressed())
    controller.button.zr.on_down(lambda _: window.bottom_right_shoulder_button.toggle_pressed())
    controller.button.zr.on_up(lambda _: window.bottom_right_shoulder_button.toggle_pressed())
    # fmt: on

    app = QApplication(sys.argv)
    window = XboxControllerOverlay()
    window.show()

    controller_thread = threading.Thread(target=controller.run)
    controller_thread.start()

    app.exec()
    controller.running = False
    controller_thread.join()
