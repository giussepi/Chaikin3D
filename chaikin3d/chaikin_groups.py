# Chaikin3D - Groups module
from __future__ import annotations
from collections.abc import Iterable

import chaikin3d.edge as E
import chaikin3d.node as N
from chaikin3d import matrix
from chaikin3d.dataholders import VirtualSet


class Group:
    """
    A Chaikin Group is a collection of nodes that make up a face in a mesh.

    A Chaikin Group is a collection of nodes that make up a face in a polyhedron.
    All the nodes in a group share the same 2D plane. When ordered in a circle-like
    list, the group is called an Ordered Group (OGroup). When applying the Chaikin3D
    algorithm to a mesh, new Groups appear. Each node of the the mesh is the
    source of one new Group in the final mesh. All existing Groups see their size
    (number of nodes) double. When a node gives birth to a Chaikin Group, its size
    is equal to the number of (main-)edges of that node (at least 3).

    Once ordered, a the graphical edges can easily be made (see 'inter_connect').
    To order a group, once must be sure of having added all the nodes that correspond
    to the specific face.

    """

    def __init__(self, iterable: Iterable, do_order: bool = False):
        self.nodes: VirtualSet[N.Node] = VirtualSet(iterable)
        self.ogroup = None
        self.ordered = False
        self.size = self.nodes.size
        self._triangles: list[N.Triangle] = None
        # assert self.size > 2 # >= 3
        if do_order:
            self.order()

    def __str__(self) -> str:
        return "[{}] o: {} s: {}".format(
            ", ".join(map(str, self.nodes)), self.ordered, self.size
        )

    def __repr__(self) -> str:
        return str(self)

    def __len__(self):
        return self.size

    def __iter__(self):
        return iter(self.ogroup) if self.ordered else iter(self.nodes)

    def __getitem__(self, index: int):
        if self.ordered:
            return self.ogroup[index]
        return self.nodes[index]

    @property
    def triangles(self) -> list[N.Triangle]:
        assert self._triangles is not None, "Group has not been interconnected"
        return iter(self._triangles)

    def order(self, force: bool = False) -> None:
        """
        Order a Group.

        Order a Group based on node inter-connectivity. We start be taking a
        node (any node), and looking for nodes in this Group in its main edges.
        Once such a node/edge is found, we can propagate to this node, until
        we meet the starting node.
        Sets the 'ordered' attribute to True.

        Args:
            force (bool):
                force the ordering algorithm, even tho the 'ordered'
                attribute is set to True.

        Raises:
            Exception: Broken Group (the nodes do not form a face).

        """

        if not force and self.ordered:
            return
        # trivial case
        if self.size < 3:
            self.ogroup = self.nodes
            self.ordered = True
            return
        # initialize variables
        group_list: list[N.Node] = list(self.nodes)
        current_node = group_list.pop()
        self.ogroup = [current_node]
        # connect the next ones (don't care if we go 'left' or 'right')
        while group_list:
            for index, remaining_node in enumerate(group_list):
                if E.Edge.are_connected(current_node, remaining_node, "main"):
                    self.ogroup.append(remaining_node)
                    current_node = remaining_node
                    group_list.pop(index)
                    break
            else:
                print("current_node")
                _debug_print_full_node(current_node)
                print("group_list")
                _debug_print_full_nodes(group_list)
                print("ordered group")
                _debug_print_full_nodes(self.ogroup)
                print("group")
                _debug_print_full_nodes(self.nodes)
                # raise Exception('broken group')
                print(
                    f"Warning: broken group found. attaching remaning nodes: {len(group_list)}"
                )
                self.ogroup.extend(group_list)
                raise Exception("Broken group (see stdout for more info)")

        self.ordered = True

    def cycle_connect(self, edge_type: str = "main") -> None:
        """
        Connect the nodes the Group in a circular manner.
        The nodes are supposed to be already-ordered in a non-ordered Group.

        Args:
            edge_type (str): Edge type: "main" or "graphical".

        """

        for i in range(self.size - 1):
            self.nodes[i].connect(self.nodes[i + 1], edge_type)
        self.nodes[-1].connect(self.nodes[0], edge_type)

    def inter_connect(
        self, edge_type: str = "graphical", order_first: bool = False
    ) -> None:
        """
        Create the required graphical edges between the nodes.

        Create the required graphical edges between the nodes in a way
        that the smallest amount of edges is created.

        Args:
            edge_type (str) : Edge type: "main" or "graphical".
            order_first     (bool): Call the 'order' method first ?

        Raises:
            AssertionError: The Group is NOT ordered (maybe set 'order_first' to True).

        """

        if order_first:
            self.order(True)
        assert self.ordered
        num_iter = int(matrix.np.log2(self.size)) - 1
        #
        for x in range(num_iter):
            step = 2 ** (x + 1)
            prev_node = self.ogroup[0]
            for i in range(step, self.size, step):
                current_node = self.ogroup[i]
                prev_node.connect(current_node, edge_type)
                prev_node = current_node
            # connect last one to first one
            self.ogroup[0].connect(prev_node, edge_type)

    def calc_triangles(self) -> None:
        assert self._triangles is None, "Triangles already calculated"
        self._triangles = VirtualSet()
        for node1 in self.nodes:
            for node2 in (n for n in node1.partners if n in self.nodes):
                for node3 in (
                    n for n in node2.partners if n in self.nodes and n in node1.partners
                ):
                    self._triangles.add(N.Triangle(node1, node2, node3))
