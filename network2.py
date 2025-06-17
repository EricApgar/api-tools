from typing import Callable
import threading
import queue

import networkx as nx
import matplotlib.pyplot as plt

from node import GenericNode  # Assumes this exists and handles threading + callback


class Network:
    def __init__(self):
        self.graph = nx.Graph()
        self.nodes = {}
        self.node_positions = None

        self.callback_plot_network = None

        self.queue_update_plot = queue.Queue()
        self.pending_update = False

        self.flag_queue_status = threading.Event()
        self.thread_manage_plot_queue = threading.Thread(target=self.manage_plot_queue, daemon=True)


    def add_node(self, node: GenericNode):
        self.graph.add_node(node.name)
        self.nodes[node.name] = node
        self.node_positions = nx.spring_layout(self.graph)  # Update layout

        return


    def start(self):
        for node in self.nodes.values():
            node.start()
        self.flag_queue_status.set()
        self.thread_manage_plot_queue.start()

        return
    

    def stop(self):
        for node in self.nodes.values():
            node.stop()
        self.flag_queue_status.clear()
        self.thread_manage_plot_queue.join()

        return
    

    def set_callback_plot_network(self, callback: Callable):
        self.callback_plot_network = callback
        
        return
    

    def manage_plot_queue(self):
        while self.flag_queue_status.is_set():
            try:
                _ = self.queue_update_plot.get(timeout=0.1)
                self.pending_update = True
            except queue.Empty:
                continue

        return


    def add_plot_to_queue(self, node: GenericNode = None):
        self.queue_update_plot.put(self)

        return


class NetworkVisualizer:
    def __init__(self, ax: plt.Axes):
        self.ax = ax


    def plot_node(self, network: Network):
        self.ax.clear()
        nx.draw(
            network.graph,
            ax=self.ax,
            pos=network.node_positions,
            node_color='blue',
            with_labels=True,
            node_size=3000)
        
        self.ax.figure.canvas.draw()

        return

# -----------------------
# Main testing block
# -----------------------

if __name__ == '__main__':
    import time
    from matplotlib.animation import FuncAnimation

    # Create plot
    figure, ax = plt.subplots(figsize=(8, 6))
    visualizer = NetworkVisualizer(ax=ax)
    network = Network()

    network.set_callback_plot_network(visualizer.plot_node)

    # Add a single test node with latency
    node = GenericNode(name='Node 0', callback_is_active=network.add_plot_to_queue)
    node.set_comm_settings(latency_s=0.5)
    network.add_node(node)

    # Start network and background polling
    network.start()

    # Main thread animation polling
    def update_plot(_):
        if network.pending_update:
            visualizer.plot_node(network)
            network.pending_update = False

    anim = FuncAnimation(figure, update_plot, interval=100)

    try:
        plt.show()  # This blocks and runs the event loop
    finally:
        network.stop()
