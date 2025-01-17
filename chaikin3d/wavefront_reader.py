#
from __future__ import annotations
from chaikin3d.polyhedron import Polyhedron
import numpy as np
import os


class WaveFrontReader:
    """
    Read WaveFront a file (.obj). And parse it into a Polyhedron instance.

    """

    def __init__(
        self,
        path: str,
        parse_on_load: bool = True,
        rotate: bool = False,
        verbose: bool = False,
    ):
        # attributes
        self.path: str = os.path.abspath(path)
        assert os.path.isfile(self.path)
        self.vertices: list[np.array] = []
        self.vertex_indices: list[np.array] = []
        # verbosity
        self.verbose = verbose
        # parse
        if parse_on_load:
            self.parse(rotate)

    def parse(self, rotate: bool = False):
        """
        Parse the input file.

        Args:
            rotate  (bool): Invert the y and z axes.

        Raises:
            AssertionError: Invalid number of vertices in a face.

        """

        lines = open(self.path, "r").readlines()
        vertices_str = []
        vertex_indices_str = []
        for line in lines:
            # vertex line
            if line.startswith("v "):
                vertices_str.append(line[2:])
            elif line.startswith("f "):
                vertex_indices_str.append(line[2:])

        if self.verbose:
            print("obj file -> num vertices:", len(vertices_str))
            print("obj file -> num groups:", len(vertex_indices_str))

        for vertex_str in vertices_str:
            raw_vert = list(filter(None, vertex_str.split()))
            x, y, z = raw_vert[:3]
            raw_vert = (
                (x, z, y) if rotate else (x, y, z)
            )  # needed, because there is some sort of rotatiton ?
            # assert len(raw_vert) == 3 # could be 4 bc of w ( = 1.0)
            self.vertices.append(np.fromiter(map(float, raw_vert), dtype=np.float32))

        for vertex_index_str in vertex_indices_str:
            raw_vert_index = list(filter(None, vertex_index_str.split()))
            vertex_list = list(
                map(lambda s: int(s.split("/")[0]) - 1, raw_vert_index)
            )  # - 1 because indexes are starting at 1 in .obj files
            num_vertices = len(raw_vert_index)
            assert (
                num_vertices > 2
            ), f"Number of vertices are less than two: {num_vertices} > 2"  # >= 3
            self.vertex_indices.append(
                np.fromiter(
                    (vertex_list[i] for i in range(num_vertices)), dtype=np.uint16
                )
            )

    def to_polyhedron(self) -> Polyhedron:
        """
        Returns a Polyhedron instance based on the input file vertices and vertex-indices.

        Returns:
            Polyhedron: Generated Polyhedron instance.

        """

        return Polyhedron.from_standard_vertex_lists(
            self.vertices, self.vertex_indices, self.verbose
        )
