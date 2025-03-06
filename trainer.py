import sys
from PySide6.QtWidgets import QApplication
from controller import Controller
import threading
import asyncio

from controller_overlay import ControllerOverlay
from config import Config
from controller import ControllerButtonName


class Trainer:
    """
    The trainer is a helper class to highlight buttons that should be pressed next and
    unhighlight them when they are pressed
    """

    def __init__(self, controller_overlay: ControllerOverlay, controller: Controller):
        self.controller_overlay = controller_overlay
        self.controller = controller

    async def next(self, *button_names: ControllerButtonName):
        """
        Set the buttons to be highlighted. Run async. Return when the buttons are pressed
        """
        self.controller_overlay.highlight_buttons(button_names)
        future = asyncio.get_event_loop().create_future()

        def on_button_press(buttons):
            print("Pressed")
            self.controller_overlay.highlight_buttons([])
            self.controller.multi_button_events.remove_event_listener(listener_id)
            future.set_result(None)

        listener_id = self.controller.multi_button_events.add_event_listener(
            "down",
            button_names,
            on_button_press,
        )

        await future


async def train(trainer: Trainer):
    print("Training started")
    await trainer.next("face_right", "shoulder_l")
    print("Training next")
    await trainer.next("face_left", "shoulder_l")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControllerOverlay()
    config = Config.load_config()
    window.show()

    controller = Controller(config)

    window.init_controller_event_listeners(controller)

    trainer = Trainer(window, controller)

    controller_thread = threading.Thread(target=controller.run)
    controller_thread.start()

    trainer_thread = threading.Thread(target=asyncio.run, args=(train(trainer),))
    trainer_thread.start()

    app.exec()
    controller.running = False
    controller_thread.join()
