# Chaikin3D - Polyhedron module
from __future__ import annotations
import node as N
import edge as C
import matrix
import numpy as np
import sys, time
from chaikin_groups import Group
from dataholders import VirtualDict, VirtualSet
from copy import deepcopy

matrix.EPSILON = 10e-6
VERBOSE_STEP = 10


class Polyhedron:
    """
    A Polyhedron, or mesh / 3D polygon is a set of nodes and vertices that form
    a 3D shape.

    """

    def __init__(self, nodes: list[N.Node], groups: VirtualSet = None):
        self.nodes = nodes
        self.groups = groups

    def __str__(self):
        return "\n* ".join(map(str, self.nodes))

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, index: int):
        return self.nodes[index]

    def __iter__(self):
        return iter(self._iter_triangles())

    def _iter_triangles(self, type_: str = "any") -> VirtualSet:
        triangle_set = VirtualSet()
        for node in self.nodes:
            for triangle in node.get_triangles(type_):
                # add the triangle. if there is alreadw this triangle in the set, it will not be added
                triangle_set.add(triangle)
        print("num triangles (" + str(type_) + ")", triangle_set.size)
        return triangle_set

    def _set_recursion_limit(self):
        sys.setrecursionlimit(10 ** 6)

    def get_edges(self, type_: str = "any") -> list[C.Edge]:
        """
        Returns the list of edges in the polyhedron.

        Args:
            type_ (str): Type of the edges ("main", "graphical", "any").

        Returns:
            list[Edge]: List of edges in the polyhedron.

        """

        edge_list = []
        for node in self.nodes:
            for conn in node.get_edges_by_type(type_):
                if conn not in edge_list:
                    edge_list.append(conn)
        print("num edges (" + type_ + ")", len(edge_list))
        return edge_list

    @staticmethod
    def from_standard_vertex_lists(
        vertex_list: list[np.array], vertex_index_list: list[np.array]
    ) -> Polyhedron:
        """
        Returns a Polyhedron instance based on a list of vertices and a list
        of vertex-indices.

        Args:
            vertex_list       (list[np.array]): Vertices.
            vertex_index_list (list[np.array]): Vertex-indices.

        Returns:
            Polyhedron: Generated polyhedron object.

        """

        # build nodes
        nodes: list[N.Node] = list(map(N.Node.from_point, vertex_list))
        groups: VirtualSet = VirtualSet()
        to_connect = []
        # connect using the index list
        for i in range(len(vertex_index_list)):
            # get the indices
            node_groupe_index_list = vertex_index_list[i]
            # get the corresponding (ordered) group
            group = Group([nodes[index] for index in node_groupe_index_list])
            # connect the main edges (circular edge)
            group.cycle_connect("main")
            # order the group (should already be orderer tho -> else the cycle edge would fuck everything up)
            group.order()
            # connect later
            if group.size > 3:
                to_connect.append(group)
            # add group to list
            groups.add(group)

        # connect later
        for ogroup in to_connect:
            # connect the graphical edges
            # ogroup.order() -> order_first = True
            ogroup.inter_connect("graphical", order_first=True)

        # return polyhedron
        return Polyhedron(nodes, groups)

    def Chaikin3D(self, n: int = 4, verbose: bool = False) -> Polyhedron:
        """
        Apply the Chaikin3D Algorithm to this polyhedron and return the new Polyhedron.

        ...

        Args:
            n       (int): Chaikin coefficient (could be float ?).
            verbose (str): Verbose mode.

        Returns:
            Polyhedron: Polyhedron which was generated by this algorithm.

        """

        vprint = (lambda *a, **k: print(*a, **k)) if verbose else (lambda *a, **k: None)
        # change recursion limit
        self._set_recursion_limit()
        t1 = time.perf_counter()
        # init
        base_ratio = (n - 1) / n
        special_ratio = (n - 2) / (
            n - 1
        )  # when the vector has already been trunced once
        node_virt_dict: VirtualDict = VirtualDict()
        new_node_list: list[N.Node] = list()
        new_edges: list[C.Edge] = []

        vprint("Copying polyhedron data...")
        # old_polyhedron = deepcopy(self)
        old_nodes = self.nodes  # .copy()#old_polyhedron.nodes
        old_groups = (
            self.groups
        )  # .copy()	#old_polyhedron.groups # if we don't want to make the method static, but return a new polyhedron without modifying this one, should need this !
        sub_node_count = 0

        # set of groups all the groups, one group per 'old' node
        final_group_set: VirtualSet = VirtualSet()

        # count of the nodes
        total_nodes = len(self.nodes)
        # new nodes & groups
        vprint("Calculating new node positions for {} verticies".format(total_nodes))
        for node_index, current_node in enumerate(self.nodes):
            if verbose and node_index % VERBOSE_STEP == 0:
                print(
                    "[{}/{}] calculated ({:.2f}%)".format(
                        node_index, total_nodes, 100 * node_index / total_nodes
                    )
                )
            # print('\ncurrent node:', current_node)
            # create sub-nodes
            num_new_edges = num_graphical_nodes = 0
            group_set: VirtualSet = VirtualSet()
            for conn in current_node.edge_list:
                if conn.type_ == "main":
                    #
                    partner_node = conn.get_partner_node(current_node)
                    # print('\n - partner', partner_node)

                    # calculate new pos (calculations done from num_edges to current node)
                    u = matrix.vector_from_points(
                        partner_node.coords, current_node.coords
                    )
                    # get the right coefficient
                    if (
                        partner_node not in self.nodes
                    ):  # partner is one of the new nodes (already has been truncated once)
                        # print(' - special ratio')
                        ratio = special_ratio
                    else:
                        ratio = base_ratio
                    # new vector
                    v: list[float] = u * ratio
                    w = partner_node.coords + v

                    # create new N.Node & new Edge
                    sub_node = N.Node.from_point(w)
                    sub_conn = C.Edge(sub_node, partner_node, "main")

                    # re-connect edge to new node & vice-versa
                    # print(' * test\n  ->', '\n  -> '.join(map(str, partner_node.edge_list)))
                    conn.update_node(current_node, sub_node)
                    sub_node.edge_list = [conn]
                    sub_node.num_edges = 1
                    # print(' * test\n  ->', '\n  -> '.join(map(str, partner_node.edge_list)))
                    # print(' - sub_node:', sub_node)
                    # print(' - sub_node edge:', ' ; '.join(map(str, sub_node.edge_list)))

                    # add to list & increment num_new_edges
                    # print(' - adding', sub_node)
                    group_set.add(sub_node)
                    num_new_edges += 1
                elif conn.type_ == "graphical":
                    continue
                else:
                    raise Exception("Unknown edge type:", conn.type_)
            # connect all the sub-nodes together (might find something to avoid edge-crossing -> len(group_set) > 3)
            # print('group set', group_set)
            group = Group(group_set)
            # connect main edges, in a cycle-like order
            group.cycle_connect("main")
            # connect graphical together
            group.inter_connect("graphical", order_first=True)
            final_group_set.add(group)

            # add those sub-nodes to the new nodes virtual dict
            node_virt_dict[old_nodes[node_index]] = group_set.copy()
            sub_node_count += group_set.size
            # add new node to new nodes list
            new_node_list.extend(group.group)

        # Now, the variable 'final_group_set' holds 'total_nodes' group objects.
        # Every node of the given Polyhedron has exactly one corresponding group
        # This group is already inter-connected, and ordered
        # If we plot the mesh now, using the 'final_group_set' variable, we
        # would get one polygon at the position of our old nodes. The
        # surfaces of our base polyhedron would be missing.
        #
        # We are now going to add the missing graphical edges for these
        # surfaces to be drawn.

        # To re-construct the old surfaces, we need to find the new nodes that
        # are connected to these. The thing is, we can try and find them using
        # vector-space mathematics or with plane point-on-plane calculations, but
        # a more algorithmic solution is more elegant and would eradicate the
        # errors that come with floating-point number precisions etc.

        # Methodology:
        # Foreach group of old_groups :
        # 	Foreach couple of nodes in this group :
        # 		search their equivalent new nodes :
        # 			- based on distance :
        # 				The two new nodes that should be connected are the ones that are the closest to
        # 				the 'other' old node. Illustration :
        # 					------C---------------------------G----H--
        # 					------------------------------------------
        # 					-----oA--B---------------------F---oE---I-
        # 					-D-------------------------------K--------
        # 	 				--------------------------------------J---
        # 				old nodes : oA and oE (old A & old E)
        # 				new nodes that should be chosen for edge: B & F
        # 					because :
        # 						eucl_dist(B, oE) < eucl_dist(*\ {B} U nE, oE) (w/ nE = new nodes, sourcing from oE)
        # 						 <=> eucl_dist(B, oE) < eucl_dist(C, oE) and eucl_dist(B, oE) < eucl_dist(D, oE)
        # 						eucl_dist(F, oE) < eucl_dist(*\ {F} U nA, oE) (w/ nA = new nodes, sourcing from oA)
        # 						 <=> eucl_dist(F, oE) < eucl_dist(K, oE) and eucl_dist(F, oE) < eucl_dist(I, oE) and ...

        # TODO: UPDATE THIS LIST OF VARS
        # List of the existing variables that are used to reconnect the surfaces :
        # - final_group_set: (explained earlier)
        # - old_groups: groups of the Polyhedron we are trying to approximate using this algorithm
        # List of the non-existing variables that are being built/extended/used to reconnect the surfaces :
        # - final_group_set: the surface groups are going to be added to this set
        # - group_objects: list of all the surface-groups. only used to connect the groups
        # - total_old_groups: number of old groups

        # set of new (ordered) groups, one per surface
        new_group_set: VirtualSet[Group] = VirtualSet()
        # one new group per old group (talking about old-surface-groups !)
        for old_group in old_groups:
            # an old_group should be ordered, but let's make sure of it
            # if the group is already ordered, it will instantly return anyway
            old_group.order()
            new_group_node_list: list[N.Node] = list()

            # iterate over the nodes
            # we start at 1 bc we do them in pairs and we don't want
            # a node to be in 2 pairs (first and last one for example)
            for i in range(old_group.size):
                # get two nodes in group that 'follow' each other
                current_old_node = old_group.ogroup[i - 1]
                partner_old_node = old_group.ogroup[i]
                # get corresponding new node lists (one old node has multiple new nodes -> thx Chaikin)
                # 'current_old_node' corresponding new nodes
                current_old_node_corresp_new_nodes = node_virt_dict[current_old_node]
                partner_old_node_corresp_new_nodes = node_virt_dict[partner_old_node]
                # find the two nodes that are the closest to the 'other' old node
                # for the 'current_old_node_corresp_new_nodes' :
                min_dist_to_other_node: float = np.inf
                closest_new_node_1: N.Node = None
                for new_node in current_old_node_corresp_new_nodes:
                    # calculate distance to partner_old_node (this new node is sourcing from current_old_node)
                    # dist(a - b) == dist(b - a)
                    dist_to_other_node: float = np.linalg.norm(
                        new_node.coords - partner_old_node.coords
                    )
                    # new node is closer than previously found nodes
                    if dist_to_other_node < min_dist_to_other_node:
                        # update distance
                        min_dist_to_other_node = dist_to_other_node
                        # update closest node
                        closest_new_node_1 = new_node
                # for the 'current_old_node_corresp_new_nodes' :
                min_dist_to_other_node: float = np.inf
                closest_new_node_2: N.Node = None
                for new_node in partner_old_node_corresp_new_nodes:
                    # calculate distance to current_old_node (this new node is sourcing from partner_old_node)
                    dist_to_other_node: float = np.linalg.norm(
                        new_node.coords - current_old_node.coords
                    )
                    # new node is closer than previously found nodes
                    if dist_to_other_node < min_dist_to_other_node:
                        # update distance
                        min_dist_to_other_node = dist_to_other_node
                        # update closest node
                        closest_new_node_2 = new_node
                # assert that nodes were found (no empty group)
                assert closest_new_node_1 and closest_new_node_2

                # add 'closest_new_node_1' & 'closest_new_node_1' to the new group node list
                new_group_node_list.append(closest_new_node_1)
                new_group_node_list.append(closest_new_node_2)

            # create new (already ordered) group
            new_group: Group = Group(new_group_node_list)
            new_group.ordered = True
            new_group.ogroup = new_group_node_list.copy()

            # add group to new groups
            new_group_set.add(new_group)

        num_new_groups = len(new_group_set)
        vprint("Connecting the surface groups ({})".format(num_new_groups))
        for i, group in enumerate(new_group_set):
            if verbose and i % VERBOSE_STEP == 0:
                print(f"[{i}/{num_new_groups}] connected ({100*i/num_new_groups:.2f}%)")
            group.inter_connect("graphical")

        # Merge groups together
        final_group_set.merge_with(new_group_set)

        # return the final polyhedron
        vprint(
            "Chaikin 3D iteration finished {} nodes in {:.3} sec".format(
                num_new_groups, time.perf_counter() - t1
            )
        )
        return Polyhedron(new_node_list, final_group_set)

    @staticmethod
    def _nec_group_cond(group):
        assert type(group) == VirtualSet
        num_elements = group.size
        for i in range(num_elements):
            for j in range(i + 1, num_elements):
                if not C.Edge.are_connected(group[i], group[j], "main"):
                    return False
        return True

    @staticmethod
    def _find_chaikin_groups_for_node(chaikin_node: N.Node) -> list[VirtualSet]:
        chaikin_group_set_list: list[VirtualSet] = []
        main_edges = chaikin_node.get_edges_by_type("main")
        num_main_edges = len(main_edges)

        for i in range(num_main_edges):
            #
            second_node = main_edges[i].get_partner_node(chaikin_node)
            for j in range(num_main_edges):
                if i == j:
                    continue
                #
                end_node = main_edges[j].get_partner_node(chaikin_node)
                plane = matrix.Plane.from_points(
                    chaikin_node.coords, second_node.coords, end_node.coords
                )
                #
                for sub_conn in second_node.get_edges_by_type("main"):
                    partner_node = sub_conn.get_partner_node(second_node)
                    local_group_set_list: list[
                        VirtualSet
                    ] = Polyhedron._rec_find_chaikin_group_with_plane(
                        chaikin_node,
                        end_node,
                        second_node,
                        partner_node,
                        VirtualSet([end_node, chaikin_node, second_node]),
                        plane,
                    )
                    for local_group in local_group_set_list:
                        if local_group not in chaikin_group_set_list:
                            chaikin_group_set_list.append(local_group)

        return chaikin_group_set_list

    @staticmethod
    def _rec_find_chaikin_group_with_plane(
        start_node: N.Node,
        end_node: N.Node,
        second_node: N.Node,
        current_node: N.Node,
        current_group: VirtualSet,
        plane: matrix.Plane,
        depth: int = 0,
    ) -> list[VirtualSet]:

        # end of group ?
        if current_node == end_node:
            return [current_group]
        # invalid node ?
        if current_node in current_group or not plane.point_on_plane(
            current_node.coords
        ):
            return []
        """
		else:
			for i in range(len(current_group) - 1):
				if not C.Edge.are_connected(current_group[i], current_group[i + 1], 'main'):
					raise Exception('hm')
				if i > 2:
					if current_group[i].coords in map(lambda n: n.coords, list(current_group[:i]) + list(current_group[i+1:])):
						raise Exception('hm2')
			if not all([plane.point_on_plane(node.coords) for node in current_group]):
				print('yes')
			print(len(current_group))
		"""

        # add to group
        current_group.add(current_node)

        # continue search
        local_group_set_list: list[VirtualSet] = []
        for conn in current_node.get_edges_by_type("main"):
            partner_node = conn.get_partner_node(current_node)
            # sub_local_group_set_list are the chaikin groups that go through the partner_node (long & complicated name for something very simple)
            sub_local_group_set_list = Polyhedron._rec_find_chaikin_group_with_plane(
                start_node,
                end_node,
                second_node,
                partner_node,
                current_group.copy(),
                plane,
                depth + 1,
            )
            # add unique groups
            for group in sub_local_group_set_list:
                if group not in local_group_set_list:
                    local_group_set_list.append(group)

        return local_group_set_list


#