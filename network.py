from typing import Callable
import threading
import queue

import networkx as nx
import matplotlib.pyplot as plt

from node import GenericNode


class Network():

    def __init__(self):
        
        self.graph = nx.Graph()
        self.nodes = {}
        self.node_positions = None

        self.callback_plot_network = None
        self.flag_queue_status = threading.Event()
        self.queue_update_plot = queue.Queue()
        self.thread_manage_plot_queue = threading.Thread(target=self.manage_plot_queue)


    def add_node(self, node: GenericNode):

        self.graph.add_node(node.name)
        self.nodes[node.name] = node
        self.node_positions = nx.spring_layout(self.graph)

        return
    

    def start(self):

        for node in self.nodes:
            self.nodes[node].start()

        self.flag_queue_status.set()
        self.thread_manage_plot_queue.start()

        return
    

    def stop(self):

        for node in self.nodes:
            self.nodes[node].stop()

            self.flag_queue_status.clear()
            self.thread_manage_plot_queue.join()

        return
    

    def set_callback_plot_network(self, callback: Callable):

        self.callback_plot_network = callback

        return
    

    def manage_plot_queue(self):

        while self.flag_queue_status.is_set():
            if self.queue_update_plot.qsize() > 0:
                network = self.queue_update_plot.get(timeout=0.1)
                self.callback_plot_network(network)

        return
    

    def add_plot_to_queue(self, node: GenericNode=None):

        self.queue_update_plot.put(self)

        return
    

class NetworkVizualizer():

    def __init__(self, ax: plt.Axes):
        
        self.ax = ax

        plt.ion()


    def plot_node(self, network: Network):

        self.ax.clear()

        nx.draw(
            network.graph,
            ax=self.ax,
            pos=network.node_positions,
            node_color='blue',
            with_labels=True,
            node_size=3000)
        
        plt.pause(0.05)

        return
    

if __name__ == '__main__':

    import time

    plt.ion()
    figure, ax = plt.subplots(figsize=(8, 6))
    graph = nx.Graph()
    graph.add_node('Test')
    nx.draw(graph, ax=ax, node_color='red', with_labels=True, node_size=2000)
    plt.show()
    plt.pause(1)

    v = NetworkVizualizer(ax=ax)
    n = Network()

    n.set_callback_plot_network(v.plot_node)
    node = GenericNode(name='Node 0', callback_is_active=n.add_plot_to_queue)
    node.set_comm_settings(latency_s=.5)
    n.add_node(node=node)

    n.start()
    time.sleep(10)
    n.stop()

    pass
