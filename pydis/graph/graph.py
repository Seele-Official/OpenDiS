"""@package docstring
portable-graph-utilities
a lightweight and extensible object-oriented graph model for python

https://github.com/maxcai314/portable-graph-utilities
Max Cai
maxster@xz.ax
"""


class Node:
    def __init__(self):
        self._edges = set()

    def edges(self):
        return iter(self._edges)

    def num_neighbors(self):
        return len(self._edges)

    def _register_edge(self, edge):
        self._edges.add(edge)

    def _deregister_edge(self, edge):
        self._edges.discard(edge)


class Edge:
    def __init__(self, source: Node, target: Node):
        self._source = source
        self._target = target

    @property
    def source(self):
        return self._source

    @property
    def target(self):
        return self._target

    def __repr__(self) -> str:
        return f"({self.source} -> {self.target})"


class Graph:
    def __init__(self):
        self._nodes = set()
        self._edges = {}

    def clear(self):
        for node in self._nodes:
            node._edges.clear()
        self._nodes.clear()
        self._edges.clear()

    def add_node(self, node: Node):
        self._nodes.add(node)

    def remove_node(self, node: Node):
        for edge in node.edges():
            other_node = edge.source if edge.source != node else edge.target
            other_node._deregister_edge(edge)
            self._edges.pop((edge.source, edge.target), None)
            self._edges.pop((edge.target, edge.source), None)
        node._edges.clear()
        self._nodes.remove(node)

    def has_node(self, node: Node):
        return node in self._nodes

    def nodes(self):
        return iter(self._nodes)

    def add_edge(self, edge: Edge):
        if self.has_edge(edge):
            raise ValueError("Edge already exists between nodes")

        edge.source._register_edge(edge)
        edge.target._register_edge(edge)
        self._edges[edge.source, edge.target] = edge

    def remove_edge(self, edge: Edge):
        edge.source._deregister_edge(edge)
        edge.target._deregister_edge(edge)
        self._edges.pop((edge.source, edge.target), None)
        self._edges.pop((edge.target, edge.source), None)

    def has_edge(self, edge: Edge):
        return self.has_edge_between(edge.source, edge.target)

    def has_edge_between(self, source: Node, target: Node):
        return (source, target) in self._edges or (target, source) in self._edges

    def edge_between(self, source: Node, target: Node):
        return self._edges.get((source, target), None) or self._edges.get((target, source), None)

    def edges(self):
        return self._edges.values()

    def __repr__(self) -> str:
        return f"Graph(nodes={self._nodes}, edges={self._edges.values()})"
