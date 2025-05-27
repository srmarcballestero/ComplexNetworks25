import numpy as np
import networkx as nx
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, Slider, LinearColorMapper, ColorBar, Button
from bokeh.layouts import column, row
from bokeh.transform import transform
from bokeh.palettes import Viridis256
import pickle

# ====== PARAMETERS ======
K = 0.5               # Initial coupling strength
dt = 0.1              # Time step

# ====== CREATE NETWORK ======
with open("ntw_all.pickle", "rb") as f:
    G = pickle.load(f)  # Load network from file
pos = nx.spring_layout(G)  # Position nodes
node_list = list(G.nodes())
N = len(node_list)

# ====== INITIAL CONDITIONS ======
theta = np.random.uniform(0, 2*np.pi, N)
omega = np.zeros(N)  # All oscillators identical

# ====== BOKEH SETUP ======
# Color mapper for phases (0 to 2π)
phase_mapper = LinearColorMapper(palette=Viridis256, 
                               low=0, high=2*np.pi)

# Network plot data sources
node_source = ColumnDataSource(data={
    'x': [pos[node][0] for node in node_list],
    'y': [pos[node][1] for node in node_list],
    'phase': theta
})

edge_source = ColumnDataSource(data={
    'xs': [[pos[edge[0]][0], pos[edge[1]][0]] for edge in G.edges()],
    'ys': [[pos[edge[0]][1], pos[edge[1]][1]] for edge in G.edges()]
})

# Synchronization plot data
r_source = ColumnDataSource(data={'t': [], 'r': []})

# ====== CREATE PLOTS ======
# Network plot
network_plot = figure(
    width=500, height=500,
    title="Kuramoto Model Network (Node Color = Phase)",
    tools="pan,wheel_zoom,reset"
)
network_plot.multi_line(
    xs='xs', ys='ys', 
    source=edge_source,
    line_color='gray', line_alpha=0.6
)
nodes = network_plot.circle(
    x='x', y='y', 
    size=15,
    source=node_source,
    fill_color={'field': 'phase', 'transform': phase_mapper},
    line_color='black'
)

# Add color bar
color_bar = ColorBar(color_mapper=phase_mapper, 
                    label_standoff=12,
                    location=(0,0),
                    title="Phase θ")
network_plot.add_layout(color_bar, 'right')

# Synchronization plot
sync_plot = figure(
    width=500, height=200,
    title="Synchronization (r)",
    x_range=(0, 100), y_range=(0, 1.1)
)
sync_line = sync_plot.line(x='t', y='r', 
                         source=r_source, 
                         line_width=2, color='red')

# Controls
slider = Slider(title="Coupling Strength (K)", 
               value=K, start=0.0, end=5.0, step=0.1)
reset_button = Button(label="Restart Simulation", button_type="success")

# ====== UPDATE FUNCTION ======
# Global variable for time
t = 0

def update():
    global theta, t

    K = slider.value

    new_theta = theta.copy()
    for i, n in enumerate(node_list):
        neigh = list(G.neighbors(n))
        if not neigh:
            continue
        neigh_idx = [node_list.index(m) for m in neigh]
        coupling = np.sum(np.sin(theta[neigh_idx] - theta[i]))
        new_theta[i] += (K / len(neigh)) * coupling * dt

    theta[:] = new_theta % (2*np.pi)
    node_source.data.update(phase=theta)

    # Order parameter
    r = np.abs(np.sum(np.exp(1j * theta))) / N
    r_source.stream({'t': [t], 'r': [r]}, rollover=200)
    t += 1

    if t > 100:
        sync_plot.x_range.start = t - 100
        sync_plot.x_range.end = t

# ====== RESET FUNCTION ======
def reset_simulation():
    global theta, t
    theta = np.random.uniform(0, 2 * np.pi, N)
    t = 0
    node_source.data.update(phase=theta)
    r_source.data = {'t': [], 'r': []}
    sync_plot.x_range.start = 0
    sync_plot.x_range.end = 100

reset_button.on_click(reset_simulation)

# ====== LAYOUT AND RUN ======
controls = column(slider, reset_button)
layout = row(column(network_plot, sync_plot), controls)
curdoc().add_root(layout)
curdoc().add_periodic_callback(update, 100)  # Update every 100ms