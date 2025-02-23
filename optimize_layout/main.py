from load_dataset import dataset
from controller_mapping import ControllerMapping, simulate_iterations
import matplotlib.pyplot as plt


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


fig, ax, line = init_plot()

data_subset = dataset[:10000]
for i, (difficulty, best_mapping) in enumerate(
    simulate_iterations(
        ControllerMapping.random(),
        sequence=data_subset,
        batch_mutations=10,
        random_mutation_probability=0.1,
        random_mutation_every_n_iterations=5,
    )
):
    print(f"Iteration {i}: {difficulty}")
    update_plot(ax, line, i, difficulty)
    best_mapping.save(f"best_mapping.json")

plt.ioff()
plt.show()
