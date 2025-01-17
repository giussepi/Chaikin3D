# Polyhedron rendering
from __future__ import annotations
import time

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from chaikin3d.polyhedron import Polyhedron


DO_CHAIKIN = True


def gen_random_color() -> str:
    """
    A short description.

    A bit longer description.

    Args:
        variable (type): description

    Returns:
        str: Random color in the form of "#??????".

    """

    choices = list("0123456789abcdef")
    return "#" + "".join(np.random.choice(choices) for _ in range(6))


class Renderer:
    """
    Renderer for meshes.

    """

    def __init__(self, verbose: bool = False, *args, **kwargs):
        self.verbose = verbose
        self.vprint = print if verbose else lambda *args, **kwargs: None

        self.args = args
        self.kwargs = kwargs

        self.active_subplot = False
        self.subplot_fig = None
        self.subplot_row_index = 0
        self.subplot_row_limit = 0
        self.subplot_col_index = 0
        self.subplot_col_limit = 0

    def figure(self, data: list) -> _figure.Figure:
        """
        Draw the data.

        Args:
            data (list): Data to draw.

        """

        return go.Figure(data, *self.args, **self.kwargs)

    def init_subplots(self, rows: int, cols: int, *args, **kwargs) -> None:
        assert not self.active_subplot  # cannot have two subplots at a time
        assert rows > 0  # >= 1
        assert cols > 0  # >= 1
        self.active_subplot = True
        specs = [[{"type": "scene"}] * cols] * rows
        self.subplot_fig = make_subplots(
            rows=rows, cols=cols, specs=specs, *args, **kwargs
        )
        self.subplot_row_index = 1
        self.subplot_row_limit = rows
        self.subplot_col_index = 1
        self.subplot_col_limit = cols

    def fill_subplot(self, data: list, *args, **kwargs):
        assert self.active_subplot  # make sure we are actually drawing subplots
        self.subplot_fig.add_trace(
            data,
            row=self.subplot_row_index,
            col=self.subplot_col_index,
            *args,
            **kwargs,
        )
        # go to the next row ol column
        self.next_subplot()

    def add_to_subplot(
        self,
        data: list,
        function=None,
        custom_row: int = -1,
        custom_col: int = -1,
        *args,
        **kwargs,
    ):
        assert self.active_subplot  # make sure we are actually drawing subplots
        # default function if None
        if function == None:
            function = self.subplot_fig.add_trace

        # if you customize one, please customize the other too
        if custom_row != -1:
            assert custom_col != -1
        elif custom_col != -1:
            assert custom_row != -1

        function(
            data,
            row=self.subplot_row_index if custom_row == -1 else custom_row,
            col=self.subplot_col_index if custom_col == -1 else custom_col,
            *args,
            **kwargs,
        )

    def next_subplot(self) -> None:
        assert self.active_subplot
        if self.subplot_col_index == self.subplot_col_limit:
            self.subplot_col_index = 1
            self.subplot_row_index += 1
            if self.subplot_row_index > self.subplot_row_limit:
                self.active_subplot = False
                self.vprint("subplot filled")
            return
        # no limit reached
        self.subplot_col_index += 1

    def draw_subplots(self):
        self.vprint(" - drawing subplots -")
        self.subplot_fig.show()
        # don't reset figure on purpose (why do it ? could be used later by user)
        self.active_subplot = False
        self.subplot_row_index = 0
        self.subplot_row_limit = 0
        self.subplot_col_index = 0
        self.subplot_col_limit = 0
        return self.subplot_fig

    def get_polyhedron_draw_data(
        self,
        polyhedron: Polyhedron,
        type_: str = "any",
        alpha: float = 0.8,
        draw_text: bool = False,
        color: str = "lightblue",
    ) -> list[go.Mesh3d]:
        self.vprint("Reading polyhedron data for rendering")
        t1 = time.perf_counter()
        vertex_list = []
        vertex_list_length = 0
        vertex_index_list = []
        triangle_iterable = (
            polyhedron if type_ == "any" else polyhedron._iter_triangles(type_)
        )
        for triangle in triangle_iterable:
            index_list = []
            for vertex in triangle.iter_coords:
                if vertex not in vertex_list:
                    vertex_list.append(vertex)
                    vertex_list_length += 1
                    index_list.append(vertex_list_length - 1)
                else:
                    index_list.append(vertex_list.index(vertex))
            vertex_index_list.append(index_list)
        self.vprint(f"Total time for processing: {time.perf_counter() - t1:.3}s")

        if not vertex_list and not vertex_index_list:
            self.vprint("No polyhedron data")
            return []

        X, Y, Z = list(zip(*vertex_list))
        I, J, K = list(zip(*vertex_index_list))
        if color == "random":
            num_colorscales = 4
            return [
                go.Mesh3d(
                    x=X,
                    y=Y,
                    z=Z,
                    colorscale=[
                        [i / num_colorscales, gen_random_color()]
                        for i in range(0, num_colorscales + 1)
                    ],
                    intensity=np.linspace(0, 1, len(I), endpoint=True),
                    intensitymode="cell",
                    i=I,
                    j=J,
                    k=K,
                    opacity=alpha,
                )
            ]
        return [
            go.Mesh3d(
                x=X,
                y=Y,
                z=Z,
                color=color,
                i=I,
                j=J,
                k=K,
                opacity=alpha,
            )
        ]

    def draw_polyhedron(
        self, polyhedron: Polyhedron, alpha: float = 0.8, draw_text: bool = True
    ) -> None:
        fig = self.figure(
            data=self.get_polyhedron_draw_data(polyhedron, alpha, draw_text)
        )
        fig.show()
        return fig

    def get_edges_draw_data(
        self,
        polyhedron: Polyhedron,
        type_: str = "any",
        line_color: str = "yellow",
        node_color: str = "green",
        width: int = 2,
    ) -> list[go.Scatter3d]:
        # flatten a list of lists into a list
        def flatten(l): return list(y for x in l for y in x)
        # iterative code below
        xs, ys, zs = map(
            flatten,
            zip(
                *(
                    [[edge.A.coords[i], edge.B.coords[i], None] for i in range(3)]
                    for edge in polyhedron.get_edges(type_)
                )
            ),
        )
        # xs, ys, zs = [], [], []
        # for edge in polyhedron.get_edges(type_):
        #     A, B = edge.A.coords, edge.B.coords
        #     xs.extend([A[0], B[0], None])
        #     ys.extend([A[1], B[1], None])
        #     zs.extend([A[2], B[2], None])
        return [
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                marker={
                    "size": 2,
                    "color": gen_random_color()
                    if node_color == "random"
                    else node_color,
                },
                line={
                    "color": gen_random_color()
                    if line_color == "random"
                    else line_color,
                    "width": 2,
                    "dash": "solid",
                },
            )
        ]

    def draw_edges(
        self,
        polyhedron: Polyhedron,
        type_: str = "any",
        color: str = "lightblue",
        width: int = 2,
    ) -> None:
        fig = self.figure(
            data=self.get_edges_draw_data(polyhedron, type_, color, width)
        )
        fig.show()
        return fig
