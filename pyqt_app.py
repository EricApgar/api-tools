import sys
import networkx as nx
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QGraphicsView,
    QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem
)
from PyQt5.QtGui import QBrush, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QTimer

from network import Network
from node import GenericNode

# PyQt visualizer widget
class NetworkVisualizer(QGraphicsView):
    def __init__(self, network):
        super().__init__()
        self.network = network
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.radius = 20

    def update_graph(self, graph):
        self.scene.clear()
        pos = self.network.node_positions #or nx.spring_layout(graph)

        node_items = {}
        for node, (x, y) in pos.items():
            x *= 200
            y *= 200
            node_center = (x + self.radius/2, y + self.radius/2)
            node_items[node] = node_center

        # Draw edges first (behind nodes)
        for u, v in graph.edges():
            x1, y1 = node_items[u]
            x2, y2 = node_items[v]
            line = QGraphicsLineItem(x1, y1, x2, y2)
            line.setPen(QPen(Qt.black, 2))
            self.scene.addItem(line)

        # Draw nodes and labels on top
        for node, (x, y) in pos.items():
            x *= 200
            y *= 200
            ellipse = QGraphicsEllipseItem(x, y, self.radius, self.radius)
            color = 'green' if node.is_active else 'red'
            ellipse.setBrush(QBrush(QColor(color)))
            self.scene.addItem(ellipse)

            label = QGraphicsTextItem(node.name)
            label.setFont(QFont("Arial", 10))
            label.setPos(x, y - 20)
            self.scene.addItem(label)

# Main window
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Monitor")

        self.network = Network()
        self.network.set_callback_plot_network(self.on_network_update)

        self.visualizer = NetworkVisualizer(self.network)

        self.button = QPushButton("Add Node")
        self.button.clicked.connect(self.add_node)

        self.button_start = QPushButton("Start Network")
        self.button_start.clicked.connect(self.start_network)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.button_start)
        layout.addWidget(self.visualizer)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(200)

        self.node_count = 0
        # self.network.start()

    def add_node(self):
        name = f"Node {self.node_count}"
        node = GenericNode(name=name, callback_is_active=self.network.add_to_queue)
        node.set_comm_settings(latency_s=0.5)
        self.network.add_node(node=node)
        self.node_count += 1

        self.visualizer.update_graph(self.network.graph)


    def start_network(self):
        self.network.start()


    def check_queue(self):
        while not self.network.queue.empty():
            self.network.queue.get()
            self.visualizer.update_graph(self.network.graph)

    def on_network_update(self, _):
        # Called by the network when a node activity triggers a redraw
        self.network.queue.put(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
