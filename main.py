import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from controller import Controller
import threading

from controller_overlay import ControllerOverlay
from config import Config
from cursor import Cursor


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControllerOverlay()
    config = Config.load_config()
    window.show()

    controller = Controller(config)

    window.init_controller_event_listeners(controller)

    controller_thread = threading.Thread(target=controller.run)
    controller_thread.start()

    cursor = Cursor(window, controller, config)

    timer = QTimer()
    timer.setTimerType(Qt.TimerType.PreciseTimer)
    timer.timeout.connect(cursor.update)
    timer.start(16)  # Approximately 60 FPS

    app.exec()
    controller.running = False
    controller_thread.join()
