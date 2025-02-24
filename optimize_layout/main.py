from load_dataset import dataset
from controller_mapping import ControllerMapping, simulate_iterations
import matplotlib.pyplot as plt
import pynput
import time


def init_plot():
    plt.ion()
    fig, ax = plt.subplots()
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Difficulty")
    (line,) = ax.plot([], [], "r-")
    return fig, ax, line


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


fig, ax, line = init_plot()

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


best_map = ControllerMapping.random().map
best_difficulty = float("inf")
best_map_index = 0
mutate_random_after_no_change_amount = 20
number_of_mutations = 5

mapping = ControllerMapping(best_map)


class FPSCounter:
    def __init__(self):
        self.iteration_times = []

    def start(self):
        self.start_time = time.time()

    def end(self):
        end_time = time.time()
        self.iteration_times.append(end_time - self.start_time)
        if len(self.iteration_times) > 10:
            self.iteration_times.pop(0)
        if len(self.iteration_times) == 10:
            avg_fps = 1 / (sum(self.iteration_times) / 10)
            self.print_fps(avg_fps)
            return avg_fps
        return None

    def print_fps(self, avg_fps):
        print(f"Average FPS over last 10 iterations: {avg_fps:.2f}")


fps_counter = FPSCounter()

with pynput.keyboard.Listener(on_press=on_press) as listener:
    total_iterations = 0
    while running:
        local_best_difficulty = float("inf")
        fps_counter.start()
        for i, (difficulty, map) in enumerate(
            simulate_iterations(
                mapping.map,
                char_counts,
                char_pairs,
            )
        ):
            fps_counter.end()
            total_iterations += 1
            if difficulty < local_best_difficulty:
                local_best_difficulty = difficulty
                best_map = map
                best_map_index = total_iterations
            update_plot(ax, line, total_iterations, difficulty)
            if not running:
                print("Stopping")
                break
            if total_iterations - best_map_index > mutate_random_after_no_change_amount:
                mapping = mapping.mutate_random(number_of_mutations)
                break
            fps_counter.start()
        if local_best_difficulty < best_difficulty:
            best_difficulty = local_best_difficulty
            ControllerMapping(best_map).save(
                f"mappings/mapping({best_difficulty}).json"
            )

plt.ioff()
plt.show()
