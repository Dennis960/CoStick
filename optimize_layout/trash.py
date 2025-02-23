from load_dataset import DATASET_PATH, ALLOWED_CHARS
from typing import Literal


ControllerButtonName = Literal[
    "dpad_up",
    "dpad_down",
    "dpad_left",
    "dpad_right",
    "face_up",
    "face_down",
    "face_left",
    "face_right",
    "shoulder_l",
    "shoulder_r",
    "shoulder_zl",
    "shoulder_zr",
    "stick_left",
    "stick_right",
    "minus",
    "plus",
    "home",
    "capture",
]

controller_button_names: list[ControllerButtonName] = [
    "dpad_up",
    "dpad_down",
    "dpad_left",
    "dpad_right",
    "face_up",
    "face_down",
    "face_left",
    "face_right",
    "shoulder_l",
    "shoulder_r",
    "shoulder_zl",
    "shoulder_zr",
    "stick_left",
    "stick_right",
    "minus",
    "plus",
    "home",
    "capture",
]

controller_button_difficulty_map: list[tuple[set[ControllerButtonName], int]] = [
    ({"shoulder_l", "shoulder_zl"}, 3),
    ({"shoulder_r", "shoulder_zr"}, 10),
    ({"shoulder_r", "shoulder_zr", "shoulder_l", "shoulder_zl"}, 30),
]
"""A map that lists the difficulty of pressing a set of buttons at the same time. Default value is one. This list only specifies the values that are different from the default value."""

controller_button_change_difficulty_map: list[
    tuple[tuple[set[ControllerButtonName], set[ControllerButtonName]], int]
] = [
    (({"face_left"}, {"face_right"}), 2),
    (({"face_up"}, {"face_down"}), 2),
    (({"shoulder_l"}, {"shoulder_zl"}), 2),
    (({"shoulder_r"}, {"shoulder_zr"}), 3),
    (({"shoulder_l"}, {"shoulder_l", "shoulder_zl"}), 5),
    (({"shoulder_zl"}, {"shoulder_l", "shoulder_zl"}), 5),
    (({"shoulder_r"}, {"shoulder_r", "shoulder_zr"}), 8),
    (({"shoulder_zr"}, {"shoulder_r", "shoulder_zr"}), 8),
]
"""
A map that lists the difficulty of changing from one set of buttons to another
default value is 1
higher values indicate a higher difficulty (because of more movement or because of the button being less accessible)
"""

forbidden_button_combinations: list[set[ControllerButtonName]] = [
    {"face_right", "face_left"},
    {"face_up", "face_down"},
    {"face_up", "face_right"},
    {"face_up", "face_left"},
    {"face_down", "face_right"},
    {"face_down", "face_left"},
]

allowed_button_names = [
    "face_up",
    "face_down",
    "face_left",
    "face_right",
    "shoulder_l",
    "shoulder_r",
    "shoulder_zl",
    "shoulder_zr",
]

computer_keys: list[str] = list(ALLOWED_CHARS)

### Main code
import random


def powerset(iterable: list):
    from itertools import chain, combinations

    return chain.from_iterable(
        combinations(iterable, r) for r in range(len(iterable) + 1)
    )


all_allowed_button_combinations = [
    set(buttons)
    for buttons in powerset(allowed_button_names)
    if buttons
    and not any(
        forbidden.issubset(buttons) for forbidden in forbidden_button_combinations
    )
]

chars = (
    "1234567890ß!\"$%&/()=?'+#-.,*'_:;<>|{[]}\\~@€^`qwertzuiopüasdfghjklöäyxcvbnm \n"
)
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    dataset = f.read()
# transform all chars to lowercase
dataset = dataset.lower()

"""
Given the chars, the dataset and maps for
- controller_button_difficulty_map
representing the difficulty of pressing a set of buttons at the same time
- controller_button_change_difficulty_map
representing the difficulty of changing from one set of buttons to another

the following code will try to find the optimal assignment of each char to a char button combination on a controller.:
- minimizing the overall difficulty of replicating the dataset (or parts of the dataset depending on performance)

In order to do this, a random assignment of buttons to chars is created and then optimized using a simple hill climbing algorithm.
"""

AssignmentType = dict[str, set[ControllerButtonName]]


def get_button_combination_difficulty(
    button_combination: set[ControllerButtonName],
) -> int:
    total_difficulty = len(button_combination)
    for buttons, difficulty in controller_button_difficulty_map:
        if buttons.issubset(button_combination):
            total_difficulty += difficulty
    return total_difficulty


def get_button_combination_change_difficulty(
    current_buttons: set[ControllerButtonName], next_buttons: set[ControllerButtonName]
) -> int:
    # if it is the first change, the difficulty is 0
    total_difficulty = 0
    if not current_buttons:
        return total_difficulty
    # every different button adds a difficulty of 1
    buttons_in_current_but_not_in_next = current_buttons - next_buttons
    buttons_in_next_but_not_in_current = next_buttons - current_buttons
    total_difficulty += len(buttons_in_current_but_not_in_next)
    total_difficulty += len(buttons_in_next_but_not_in_current)
    for (
        map_current_buttons,
        map_next_buttons,
    ), difficulty in controller_button_change_difficulty_map:
        if (
            map_current_buttons.issubset(current_buttons)
            and map_next_buttons.issubset(next_buttons)
            and not map_current_buttons.issubset(next_buttons)
            and not map_next_buttons.issubset(current_buttons)
        ):
            total_difficulty += difficulty
    return total_difficulty


def get_assignment_difficulty(assignment: AssignmentType, text: str) -> int:
    total_difficulty = 0
    # simulate typing the first n characters of the dataset
    current_buttons = set()
    for char in text:
        total_difficulty += get_button_combination_difficulty(assignment[char])
        print(char)
        print(get_button_combination_difficulty(assignment[char]))
        total_difficulty += get_button_combination_change_difficulty(
            current_buttons, assignment[char]
        )
        print(
            get_button_combination_change_difficulty(current_buttons, assignment[char])
        )
        current_buttons = assignment[char]
    return total_difficulty


# test the get_assignment_difficulty function for the first 100 characters
# with a random assignment. Make sure no duplicates are present in the assignment


def get_random_assignment():
    all_allowed_button_combinations_copy = all_allowed_button_combinations.copy()
    random.shuffle(all_allowed_button_combinations_copy)
    return {char: all_allowed_button_combinations_copy.pop() for char in computer_keys}

def get_unused_button_combinations(assignment: AssignmentType) -> list[set[ControllerButtonName]]:
    return [button_combination for button_combination in all_allowed_button_combinations if button_combination not in assignment.values()]


def mutate_assignment(assignment: AssignmentType) -> AssignmentType:
    """Switch the assignment of a random char with a random button combination"""
    assignment = assignment.copy()
    unused_button_combinations = get_unused_button_combinations(assignment)
    random_button_combination = random.choice(all_allowed_button_combinations)
    char = random.choice(computer_keys)
    replace_button_combination = assignment[char]
    assignment[char] = random_button_combination
    if random_button_combination in unused_button_combinations:
        return assignment
    # find the replace_button_combination in the assignment and replace it with the random_button_combination
    for char, button_combination in assignment.items():
        if button_combination == random_button_combination:
            assignment[char] = replace_button_combination
            break
    return assignment

def mutate_n_times(assignment: AssignmentType, n: int) -> AssignmentType:
    for _ in range(n):
        assignment = mutate_assignment(assignment)
    return assignment

def hill_climb(assignment: AssignmentType, text: str, n: int) -> AssignmentType:
    best_assignment = assignment
    best_difficulty = get_assignment_difficulty(assignment, text)
    for _ in range(n):
        new_assignment = mutate_assignment(assignment)
        new_difficulty = get_assignment_difficulty(new_assignment, text)
        print(new_difficulty)
        if new_difficulty < best_difficulty:
            best_assignment = new_assignment
            best_difficulty = new_difficulty
    return best_assignment

assignment = get_random_assignment()
print(assignment)
assignment = hill_climb(assignment, dataset[:100], 1000)
print(assignment)