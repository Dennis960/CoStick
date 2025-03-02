# CoStick

CoStick is a tool created with pygame and pynput to control the mouse and keyboard with a nintendo switch (or similar) controller.

It fully replaces mouse and keyboard input with a controller, and is designed to be used with a controller only.

## Installation

To install CoStick, you need to have python installed on your computer.

1. Clone the repository
2. Install the required packages with `pip install -r requirements.txt`
3. Run the program with `python main.py`

A virtual controller will appear on the screen. As soon as you connect a controller, it will be recognized and button presses as well as joystick movements will be displayed on the screen.

## Configuration

The configuration is handled by [config.py](config.py). Here you can change the keybindings and the sensitivity of the joystick.

## Controller API

The controller is separated into two parts: Buttons and Joysticks.

### Buttons

A button can trigger the following events:

- `down`: The button is pressed
- `up`: The button is released
- `click`: The button is pressed and released within the configured `single_click_duration`
- `double_click`: The button is clicked twice within the configured `double_click_duration`
- `tripple_click`: The button is clicked three times within the configured `double_click_duration`
- `long_press`: The button is pressed for longer than the configured `long_press_duration` and then released

### Joysticks

A joystick can trigger the following events:

- `move`: The joystick is moved (movements within the configured `deadzone` are ignored)

### Controller Mapping

In order for the app to know which button is where, a custom mapping can be applied inside the config.

Each controller button gets assigned an index according to pygame's controller mapping.

Each joystick gets assigned an axis according to pygame's controller mapping.

The mapping can be adjusted inside `button_mapping` and `stick_mapping` in the config.

## Basic Concept

The app uses `modes` to determine what the controller should do.

Each `mode` has a set of `button_actions`, `stick_actions` and `multi_button_actions`.

### Button Actions

A `button_action` is a function that is called when a button event is triggered.

### Stick Actions

A `stick_action` is a function that is called when a joystick event is triggered.

### Multi Button Actions

A `multi_button_action` is a function that is called when a combination of buttons is pressed.

It has the same events as a button.

### Actions

Each triggering event can be assigned to one or more actions.

An action is a function that is called when the event is triggered.

Some examples:

- `ComputerKeyDownAction(key="x")`: Presses the key "x" on the computer
- `ComputerMouseMoveAction()`: Moves the mouse on the computer
- `SwitchModeAction(mode="mode_name")`: Switches to the mode "mode_name"

Not every action type is available for every event. For example, a navigation event such as `click` can not trigger a `ComputerMouseMoveAction`.

Actions are therefore split into three groups:

- `ComputerAction`: Actions that can be executed with a simple button press
- `ComputerNavigationAction`: Actions that can be executed with a navigation event such as `move`
- `SwitchModeAction`: Actions that switch the mode

## Layout optimization

In order to optimize the assignment of keyboard keys to button combinations, an optimization script was used.

The code for the optimization can be found in the [optimize_layout](optimize_layout) folder.

The optimization script was written to minimize the average effort needed to type a given text, in this case specifically code segments of different programming languages.
