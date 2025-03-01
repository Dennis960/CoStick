from load_dataset import dataset
from controller_mapping import ControllerMapping, simulate_iterations
import matplotlib.pyplot as plt
import pynput
import multiprocessing
from typing import Callable


def clean_dataset(dataset: str):
    # remove spaces
    dataset = dataset.replace(" ", "")
    # remove newlines
    dataset = dataset.replace("\n", "")
    # remove tabs
    dataset = dataset.replace("\t", "")
    return dataset


running = True


def on_press(key: pynput.keyboard.KeyCode):
    global running
    if key.char == "q":
        running = False
        return False


pynput.keyboard.Listener(on_press=on_press).start()


data_subset = clean_dataset(dataset)

# Count chars
char_counts: dict[str, int] = {}
for char in data_subset:
    char_counts[char] = char_counts.get(char, 0) + 1
# Count how often each pair of characters occurs in the sequence
char_pairs: dict[tuple[str, str], int] = {}
for i in range(len(data_subset) - 1):
    char_pair = (data_subset[i], data_subset[i + 1])
    char_pairs[char_pair] = char_pairs.get(char_pair, 0) + 1


def run_optimization(new_best_callback: Callable[[int, int], None]):
    best_map = ControllerMapping.random().map
    best_difficulty = 999999999

    mapping = ControllerMapping(best_map)
    total_iterations = 0
    while running:
        local_best_difficulty = 999999999
        for i, (difficulty, map) in enumerate(
            simulate_iterations(mapping.map, char_counts, char_pairs)
        ):
            total_iterations += 1
            if difficulty == local_best_difficulty:
                mapping = ControllerMapping.random()
                break
            local_best_difficulty = difficulty
            best_map = map
            new_best_callback(total_iterations, difficulty)
            if not running:
                print("Stopping")
                break
        if local_best_difficulty < best_difficulty:
            best_difficulty = local_best_difficulty
            ControllerMapping(best_map).save(
                f"mappings/mapping({best_difficulty}).json"
            )


num_rows = 3
num_cols = 4


def init_plot():
    plt.ion()
    fig, axs = plt.subplots(num_rows, num_cols)
    fig.set_size_inches(12, 9)
    for ax in axs.flat:
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Difficulty")
    (line,) = axs[0, 0].plot([], [], "r-")
    return fig, axs, line


def update_plot(ax: plt.Axes, line: plt.Line2D, iteration: int, difficulty: float):
    xdata = line.get_xdata()
    ydata = line.get_ydata()
    xdata = list(xdata) + [iteration]
    ydata = list(ydata) + [difficulty]
    line.set_xdata(xdata)
    line.set_ydata(ydata)
    ax.relim()
    ax.autoscale_view()
    plt.draw()
    plt.pause(0.01)


fig, axs, line = init_plot()

run_optimization(
    lambda iteration, difficulty: update_plot(axs[0, 0], line, iteration, difficulty)
)
