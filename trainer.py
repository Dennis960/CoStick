# This script is intended to train writing text with the controller
# It will show a text and highlight the buttons that need to be pressed
# It will start with a small set of the most common letters and gradually increase the difficulty

import sys
from PySide6.QtWidgets import QApplication
from controller import Controller
import threading

from controller_overlay import ControllerOverlay
from config import Config


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControllerOverlay()
    config = Config.load_config()
    window.show()

    controller = Controller(config)

    window.init_controller_event_listeners(controller)

    controller_thread = threading.Thread(target=controller.run)
    controller_thread.start()

    app.exec()
    controller.running = False
    controller_thread.join()
