import os
import sys
from typing import Callable, List
import threading
import queue
import socket

import networkx as nx
import matplotlib.pyplot as plt

from node import Node, GenericNode


class Network():

    def __init__(self):
        
        self.graph: nx.Graph = nx.Graph()
        self.nodes: dict = {}
        self.node_positions: dict = None

        self.callback: Callable = None
        
        self.queue = queue.Queue()
        self.thread_queue = threading.Thread(target=self.manage_queue)
        self.flag_thread_queue = threading.Event()

    def add_node(
        self,
        node: Node=None,
        name: str=None,
        connections: List[str]=None,
        node_type: str='generic'):

        if node is not None:
            name = node.name
            node_type = None
        elif name is None:
            name = f'Node {len(self.nodes)}'
            # raise ValueError('Input arg "name" must be provided!')
        
        if self.graph.has_node(n=name):
            raise ValueError(f'Node {name} already exists!')
        
        if node_type == 'generic':
            node = GenericNode(name=name)
        elif node_type is None:
            pass
        else:
            raise ValueError('Input arg "node_type" is unsupported!')

        self.graph.add_node(node_for_adding=node)

        if connections is not None:
            for connection in connections:
                self.add_connection(node_1=name, node_2=connection)
        
        self.nodes[node.name] = node
        self.node_positions = nx.spring_layout(self.graph)

        return


    def delete_node(self, name: str):

        self.graph.remove_node(n=name)
        self.nodes.pop(name)

        self.node_positions = nx.spring_layout(self.graph)

        return
    

    def add_connection(self, node_1: str, node_2: str):

        if not self.graph.has_node(n=node_1) or not self.graph.has_node(n=node_2):
            raise ValueError('Nodes must exist to add connections!')
        
        self.graph.add_edge(u_of_edge=node_1, v_of_edge=node_2)

        self.node_positions = nx.spring_layout(self.graph)

        return
    

    def delete_connection(self, node_1: str, node_2: str):

        self.graph.remove_edge(u=node_1, v=node_2)

        self.node_positions = nx.spring_layout(self.graph)

        return


    def start(self, set_host: bool=True):

        DEFAULT_ADDRESS = '127.0.0.1'
        DEFAULT_PORT = 8000
        PORT_TRY_LIMIT = 10

        port_offset = -1

        self.flag_thread_queue.set()
        self.thread_queue.start()

        for node in self.nodes:
            if set_host:
                for i in range(PORT_TRY_LIMIT):
                    port_offset += 1
                    if self.is_endpoint_free(address=DEFAULT_ADDRESS, port=DEFAULT_PORT+port_offset):
                        break

                    if i == PORT_TRY_LIMIT-1:
                        raise ValueError('Could not find available port!')
                    
                self.nodes[node].set_host(address=DEFAULT_ADDRESS, port=DEFAULT_PORT+port_offset)

            self.nodes[node].start()

        return
    

    def stop(self):

        for node in self.nodes:
            self.nodes[node].stop()

        self.flag_thread_queue.clear()
        self.thread_queue.join()

        return
    

    def set_callback_plot_network(self, callback: Callable):

        self.callback = callback

        return

    
    def manage_queue(self):
        
        while self.flag_thread_queue.is_set():
            if self.callback is not None:
                if self.queue.qsize() > 0:
                    network = self.queue.get(timeout=0.1)
                    self.callback(network)

        return


    def add_to_queue(self, node: GenericNode=None):

        self.queue.put(self)

        return
    

    @staticmethod
    def is_endpoint_free(address: str, port: int) -> bool:

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((address, port))
                return True
            except socket.error:
                return False
            
        return


if __name__ == '__main__':

    import time

    n = Network()

    node = GenericNode(name='Node 0', callback_is_active=n.add_to_queue)
    node.set_comm_settings(latency_s=.5)
    n.add_node(node=node)

    n.start()
    time.sleep(10)
    n.stop()

    pass
