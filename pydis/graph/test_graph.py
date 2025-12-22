"""@package docstring
portable-graph-utilities
a lightweight and extensible object-oriented graph model for python

https://github.com/maxcai314/portable-graph-utilities
Max Cai
maxster@xz.ax
"""


from graph import Node, Edge, Graph
import unittest


class NamedNode(Node):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self) -> str:
        return f"{self.name}"


class NamedEdge(Edge):
    def __init__(self, source: NamedNode, target: NamedNode, name):
        super().__init__(source, target)
        self.name = name

    def __repr__(self) -> str:
        return f"{self.name}({self.source} -> {self.target})"


class TestGraph(unittest.TestCase):
    def test_graph(self):
        graph = Graph()
        node1 = Node()
        node2 = Node()
        edge = Edge(node1, node2)

        graph.add_node(node1)
        graph.add_node(node2)

        graph.add_edge(edge)

        with self.assertRaises(ValueError):
            graph.add_edge(edge)

        self.assertTrue(graph.has_node(node1))
        self.assertTrue(graph.has_node(node2))

        self.assertTrue(edge in node1.edges())
        self.assertTrue(edge in node2.edges())

        self.assertTrue(graph.has_edge_between(node1, node2))
        self.assertTrue(graph.has_edge(edge))
        self.assertTrue(edge == graph.edge_between(node1, node2))
        self.assertTrue(edge == graph.edge_between(node2, node1))

        print(list(graph.edges()))
        print(list(graph.nodes()))
        print(graph)

        graph.remove_edge(edge)

        self.assertFalse(graph.has_edge(edge))
        self.assertFalse(graph.has_edge_between(node1, node2))
        self.assertFalse(graph.has_edge_between(node2, node1))
        self.assertFalse(edge in node1.edges())
        self.assertFalse(edge in node2.edges())

        self.assertTrue(graph.has_node(node1))
        self.assertTrue(graph.has_node(node2))

        graph.remove_node(node1)
        self.assertFalse(graph.has_node(node1))
        self.assertTrue(graph.has_node(node2))
        graph.remove_node(node2)
        self.assertFalse(graph.has_node(node2))
        self.assertFalse(graph.has_node(node1))

        assert not graph.has_node(node1)
        assert not graph.has_node(node2)

        print([e for e in graph.edges()])
        print([n for n in graph.nodes()])

    def test_custom_graph(self):
        graph = Graph()
        node1 = NamedNode("Alice")
        node2 = NamedNode("Bob")
        edge = NamedEdge(node1, node2, "Edge1")

        graph.add_node(node1)
        graph.add_node(node2)

        graph.add_edge(edge)

        with self.assertRaises(ValueError):
            graph.add_edge(edge)

        self.assertTrue(graph.has_node(node1))
        self.assertTrue(graph.has_node(node2))

        self.assertTrue(edge in node1.edges())
        self.assertTrue(edge in node2.edges())

        self.assertTrue(graph.has_edge_between(node1, node2))
        self.assertTrue(graph.has_edge(edge))
        self.assertTrue(edge == graph.edge_between(node1, node2))
        self.assertTrue(edge == graph.edge_between(node2, node1))

        print(list(graph.edges()))
        print(list(graph.nodes()))
        print(graph)

        graph.remove_edge(edge)

        self.assertFalse(graph.has_edge(edge))
        self.assertFalse(graph.has_edge_between(node1, node2))
        self.assertFalse(graph.has_edge_between(node2, node1))
        self.assertFalse(edge in node1.edges())
        self.assertFalse(edge in node2.edges())

        self.assertTrue(graph.has_node(node1))
        self.assertTrue(graph.has_node(node2))

        graph.remove_node(node1)
        self.assertFalse(graph.has_node(node1))
        self.assertTrue(graph.has_node(node2))
        graph.remove_node(node2)
        self.assertFalse(graph.has_node(node2))
        self.assertFalse(graph.has_node(node1))

        assert not graph.has_node(node1)
        assert not graph.has_node(node2)

        print([e for e in graph.edges()])
        print([n for n in graph.nodes()])


if __name__ == "__main__":
    unittest.main()
