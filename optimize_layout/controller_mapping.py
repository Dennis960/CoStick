from dataclasses import dataclass
from typing import Literal, Self
from load_dataset import ALLOWED_CHARS
from itertools import chain, combinations
import random
import json
from functools import lru_cache

ControllerButton = Literal[
    "face_up",
    "face_down",
    "face_left",
    "face_right",
    "shoulder_l",
    "shoulder_r",
    "shoulder_zl",
    "shoulder_zr",
]

controller_buttons: list[ControllerButton] = [
    "face_up",
    "face_down",
    "face_left",
    "face_right",
    "shoulder_l",
    "shoulder_r",
    "shoulder_zl",
    "shoulder_zr",
]

chars = list(set(list(ALLOWED_CHARS.lower())) - {"\t", "\n", "\b", " "})


ButtonCombination = frozenset[ControllerButton]


@dataclass(frozen=True)
class ButtonPressed:
    """Stores the pressed state of a button on the controller."""

    button: ControllerButton
    pressed: bool = True


@dataclass(frozen=True)
class NotButtonPressed:
    """Stores the not pressed state of a button on the controller."""

    button: ControllerButton
    pressed: bool = False


@dataclass(frozen=True)
class ButtonCombinationDifficulty:
    """Represents a set of buttons pressed together and its difficulty."""

    buttons: ButtonCombination
    difficulty: int


@dataclass(frozen=True)
class StateTransitionDifficulty:
    """Represents the difficulty of transitioning from one button set to another."""

    from_combination: set[ButtonPressed | NotButtonPressed]
    to_combination: set[ButtonPressed | NotButtonPressed]
    difficulty: int
    both_ways: bool = False


invalid_combinations: set[ButtonCombination] = {
    frozenset({"face_left", "face_right"}),
    frozenset({"face_up", "face_down"}),
    frozenset({"face_up", "face_right"}),
    frozenset({"face_up", "face_left"}),
    frozenset({"face_down", "face_right"}),
    frozenset({"face_down", "face_left"}),
}
"""Button combinations that are not allowed because they are impossible (or at least very hard) to press at the same time."""

invalid_single_buttons: list[ControllerButton] = {
    "shoulder_l",
    "shoulder_r",
    "shoulder_zl",
    "shoulder_zr",
}
"""Buttons that should not be pressed on their own."""


def powerset(iterable: list):
    return chain.from_iterable(
        combinations(iterable, r) for r in range(len(iterable) + 1)
    )


all_allowed_button_combinations: list[ButtonCombination] = [
    frozenset(button_combination)
    for button_combination in powerset(controller_buttons)
    if button_combination
    and not any(
        invalid_combination.issubset(button_combination)
        for invalid_combination in invalid_combinations
    )
    and not (
        len(button_combination) == 1 and button_combination[0] in invalid_single_buttons
    )
]

button_combination_difficulties: list[ButtonCombinationDifficulty] = [
    ButtonCombinationDifficulty(buttons={"shoulder_l", "shoulder_zl"}, difficulty=3),
    ButtonCombinationDifficulty(buttons={"shoulder_r", "shoulder_zr"}, difficulty=10),
    ButtonCombinationDifficulty(
        buttons={"shoulder_r", "shoulder_zr", "shoulder_l", "shoulder_zl"},
        difficulty=30,
    ),
]
transition_difficulites: list[StateTransitionDifficulty] = [
    StateTransitionDifficulty(
        from_combination={ButtonPressed("face_left")},
        to_combination={ButtonPressed("face_right")},
        difficulty=2,
        both_ways=True,
    ),
    StateTransitionDifficulty(
        from_combination={ButtonPressed("face_up")},
        to_combination={ButtonPressed("face_down")},
        difficulty=2,
        both_ways=True,
    ),
    StateTransitionDifficulty(
        from_combination={ButtonPressed("shoulder_l"), NotButtonPressed("shoulder_zl")},
        to_combination={ButtonPressed("shoulder_zl"), NotButtonPressed("shoulder_l")},
        difficulty=2,
        both_ways=True,
    ),
    StateTransitionDifficulty(
        from_combination={ButtonPressed("shoulder_r"), NotButtonPressed("shoulder_zr")},
        to_combination={ButtonPressed("shoulder_zr"), NotButtonPressed("shoulder_r")},
        difficulty=3,
        both_ways=True,
    ),
    StateTransitionDifficulty(
        from_combination={ButtonPressed("shoulder_l"), NotButtonPressed("shoulder_zl")},
        to_combination={ButtonPressed("shoulder_l"), ButtonPressed("shoulder_zl")},
        difficulty=5,
    ),
    StateTransitionDifficulty(
        from_combination={ButtonPressed("shoulder_zl"), NotButtonPressed("shoulder_l")},
        to_combination={ButtonPressed("shoulder_l"), ButtonPressed("shoulder_zl")},
        difficulty=7,
    ),
    StateTransitionDifficulty(
        from_combination={ButtonPressed("shoulder_r"), NotButtonPressed("shoulder_zr")},
        to_combination={ButtonPressed("shoulder_r"), ButtonPressed("shoulder_zr")},
        difficulty=8,
    ),
    StateTransitionDifficulty(
        from_combination={ButtonPressed("shoulder_zr"), NotButtonPressed("shoulder_r")},
        to_combination={ButtonPressed("shoulder_r"), ButtonPressed("shoulder_zr")},
        difficulty=10,
    ),
]

default_button_combination_difficulty = 1
"""Default difficulty score added for every button in the combination."""
difficulty_per_added_button = 1
"""Difficulty score to add for each button added during a combination change."""
difficulty_per_removed_button = 1
"""Difficulty score to add for each button removed during a combination change."""


@lru_cache(maxsize=None)
def get_button_combination_difficulty(button_combination: ButtonCombination) -> int:
    """Computes the difficulty of a given button combination."""
    total_difficulty = 0
    # Add one default difficulty for each button in the combination
    total_difficulty += len(button_combination) * default_button_combination_difficulty
    # Add difficulty for each combination of buttons that is in button_combination_difficulties
    for button_combination_difficulty in button_combination_difficulties:
        if button_combination_difficulty.buttons.issubset(button_combination):
            total_difficulty += button_combination_difficulty.difficulty
    return total_difficulty


@lru_cache(maxsize=None)
def get_button_combination_transition_difficulty(
    from_button_combination: ButtonCombination,
    to_button_combination: ButtonCombination,
):
    total_difficulty = 0
    # Add difficulty for each button that is added or removed
    added_buttons = to_button_combination - from_button_combination
    removed_buttons = from_button_combination - to_button_combination
    total_difficulty += len(added_buttons) * difficulty_per_added_button
    total_difficulty += len(removed_buttons) * difficulty_per_removed_button
    # Add difficulty for each combination of buttons that is in transition_difficulites
    for transition_difficulty in transition_difficulites:
        matches_from = True
        matches_to = True
        for button_state in transition_difficulty.from_combination:
            if button_state.pressed:
                if button_state.button not in from_button_combination:
                    matches_from = False
            else:
                if button_state.button in from_button_combination:
                    matches_from = False
        for button_state in transition_difficulty.to_combination:
            if button_state.pressed:
                if button_state.button not in to_button_combination:
                    matches_to = False
            else:
                if button_state.button in to_button_combination:
                    matches_to = False
        if matches_from and matches_to:
            total_difficulty += transition_difficulty.difficulty
    return total_difficulty


class ControllerMapping:
    """Represents the full mapping of characters to button combinations."""

    def __init__(self, map: dict[str, ButtonCombination] = None):
        self.map: dict[str, ButtonCombination] = map
        assert set(chars) == set(self.map.keys()), "Not all characters are mapped."
        assert len(set(self.map.values())) == len(
            self.map
        ), "Duplicate button combinations found."

    def get_button_combination(self, char: str) -> set[ControllerButton]:
        """Retrieves the button combination for a given character."""
        return self.map[char]

    def get_char_difficulty(self, char: str) -> int:
        """Computes the difficulty of typing a given character using the current assignment."""
        return get_button_combination_difficulty(self.map[char])

    def get_transition_difficulty(self, from_char: str, to_char: str) -> int:
        """Computes the difficulty of transitioning from one character to another."""
        if from_char == to_char:
            # No transition difficulty if the characters are the same
            return 0
        from_button_combination = self.map[from_char]
        to_button_combination = self.map[to_char]
        return get_button_combination_transition_difficulty(
            from_button_combination, to_button_combination
        )

    def get_difficulty_for_sequence(self, sequence: str) -> int:
        """Computes the total difficulty of typing a given sequence."""
        total_difficulty = 0
        for i in range(len(sequence) - 1):
            from_char = sequence[i]
            to_char = sequence[i + 1]
            total_difficulty += self.get_char_difficulty(to_char)
            total_difficulty += self.get_transition_difficulty(from_char, to_char)
        return total_difficulty

    def to_json(self) -> str:
        """Converts the controller mapping to a JSON string."""
        map_json = json.dumps(
            {
                char: list(button_combination)
                for char, button_combination in self.map.items()
            }
        )
        return map_json

    @classmethod
    def from_json(cls, json_string: str) -> Self:
        """Creates a controller mapping from a JSON string."""
        map: dict[str, ButtonCombination] = json.loads(json_string)
        return ControllerMapping(
            {
                char: frozenset(button_combination)
                for char, button_combination in map.items()
            }
        )

    def save(self, filename: str):
        """Saves the controller mapping to a file."""
        with open(filename, "w") as f:
            f.write(self.to_json())

    @classmethod
    def get_unused_button_combinations(
        self, map: dict[str, ButtonCombination]
    ) -> set[ButtonCombination]:
        """Returns all button combinations that are not used in the map."""
        return set(all_allowed_button_combinations) - set(map.values())

    @classmethod
    def random(cls):
        """Generates a random controller mapping."""

        # create a copy of all_allowed_button_combinations
        button_combinations = all_allowed_button_combinations.copy()
        # shuffle the list
        random.shuffle(button_combinations)
        # create a mapping of characters to button combinations
        mapping = {char: button_combinations.pop() for char in chars}
        return cls(mapping)

    @classmethod
    def mutate_map(
        cls,
        random_char: str,
        random_button_combination: ButtonCombination,
        map: dict[str, ButtonCombination],
    ) -> dict[str, ButtonCombination]:
        """Mutates a given map in place."""
        # assign the random_button_combination to the random_char
        if random_button_combination in cls.get_unused_button_combinations(map):
            map[random_char] = random_button_combination
            return map
        prev_button_combination = map[random_char]
        current_char_with_random_button_combination = next(
            (
                char
                for char, button_combination in map.items()
                if button_combination == random_button_combination
            ),
            None,
        )
        assert (
            current_char_with_random_button_combination is not None
        ), "No character with the random button combination found."
        map[current_char_with_random_button_combination] = prev_button_combination
        map[random_char] = random_button_combination
        return map

    @classmethod
    def mutate_map_at_index(
        cls, index: int, map: dict[str, ButtonCombination]
    ) -> dict[str, ButtonCombination]:
        """Mutates a single character in the map at the given index."""
        random_char = chars[index]
        random_button_combination = random.choice(all_allowed_button_combinations)
        return cls.mutate_map(random_char, random_button_combination, map)

    def mutate_at_indices(self, indices: list[int]) -> Self:
        """Mutates the current controller mapping at the given indices."""
        mutated_map = self.map.copy()
        for index in indices:
            mutated_map = self.mutate_map_at_index(index, mutated_map)
        return ControllerMapping(mutated_map)

    def mutate_random(self, n: int = 1) -> Self:
        """Mutates the current controller mapping n times at random."""
        mutated_map = self.map.copy()
        for _ in range(n):
            random_index = random.randint(0, len(chars) - 1)
            mutated_map = self.mutate_map_at_index(random_index, mutated_map)
        return ControllerMapping(mutated_map)


def get_difficulty_for_sequence(
    map: dict[str, ButtonCombination], sequence: str
) -> int:
    mapping = ControllerMapping(map)
    return mapping.get_difficulty_for_sequence(sequence)


def simulate_iterations(
    map: dict[str, ButtonCombination],
    char_counts: dict[str, int],
    char_pairs: dict[tuple[str, str], int],
    mutation_batch_size: int = 5,
):
    """
    Simulate an infinite number of iterations of the optimization algorithm.
    """
    mapping = ControllerMapping(map)
    iteration = 0
    best_mapping = mapping
    best_difficulty = float("inf")
    char_indices = list(range(len(chars)))

    while True:
        random.shuffle(char_indices)
        for i in range(0, len(char_indices), mutation_batch_size):
            batch_indices = char_indices[i : i + mutation_batch_size]
            mutated_mapping = mapping.mutate_at_indices(batch_indices)
            mutated_difficulty = 0
            for char, count in char_counts.items():
                mutated_difficulty += mutated_mapping.get_char_difficulty(char) * count
            for (from_char, to_char), count in char_pairs.items():
                mutated_difficulty += (
                    mutated_mapping.get_transition_difficulty(from_char, to_char)
                    * count
                )
            if mutated_difficulty < best_difficulty:
                best_mapping = mutated_mapping
                best_difficulty = mutated_difficulty
        mapping = best_mapping

        yield best_difficulty, best_mapping.map
        iteration += 1
