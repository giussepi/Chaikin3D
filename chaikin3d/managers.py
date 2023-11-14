# -*- coding: utf-8 -*-
""" chaikin3d/managers.py """

from chaikin3d import plotting
from chaikin3d.arg_utils import gen_arg_parser, read_args
from chaikin3d.polyhedron import Polyhedron
from chaikin3d.wavefront_reader import WaveFrontReader


__all__ = [
    'ChaikinMGR'
]


class ChaikinMGR:
    """
    Holds methods to apply the chaikin3d algorithm to a polyhedron read from an .obj file and plot the results.

    Usage:
        # reading options from command line ###################################
        # python code in chaikin3d.py
        poly = ChaikinMGR()(plot=True)
        # shell call
        python chaikin3d.py -i my_obj.obj -cg 4 -cc 4 -p evolution -oe first

        # reading options from string #########################################
        # python code in chaikin3d.py
        poly = ChaikinMGR(cmd_args='-i my_obj.obj -cg 4 -cc 4 -p evolution -oe first')(plot=True)
        # shell call
        python chaikin3d.py
    """

    def __init__(self, cmd_args: str = ''):
        super().__init__()
        assert isinstance(cmd_args, str), type(cmd_args)

        self.cmd_args = cmd_args
        self.a_args = None

    def __call__(self, *, plot: bool = False) -> Polyhedron:
        assert isinstance(plot, bool), type(plot)

        polyhedron = self.process()

        if plot:
            self.plot(polyhedron)

        return polyhedron

    def process(self) -> Polyhedron:
        arg_parser = gen_arg_parser()
        # a : command-line arguments
        self.a_args = read_args(arg_parser, cmd_args=self.cmd_args)

        # input file
        reader = WaveFrontReader(self.a_args.input, True, self.a_args.rotate_mesh, self.a_args.verbosity)
        poly = reader.to_polyhedron()

        return poly

    @staticmethod
    def save_poly(poly, figure, output):
        # writing to file
        if not output:
            return
        print(f"Saving file to {output!r}")
        if output.endswith(".obj"):
            with open(output, "w") as f:
                poly.save(f)
        elif output.endswith(".html"):
            assert figure is not None, "Must plot the mesh when saving to html"
            figure.write_html(output)
        else:
            raise ValueError(f'Invalid output: "{output}"')

    def plot(self, poly: Polyhedron):
        assert isinstance(poly, Polyhedron), type(poly)

        vprint = print if self.a_args.verbose else lambda *args, **kwargs: None

        # create a renderer
        Renderer = self.a_args.renderer_class
        renderer = Renderer(verbose=self.a_args.verbose)

        # do chaikin generations before any graphics ?
        if self.a_args.plot != "evolution" and self.a_args.plot != "animation":
            assert (
                self.a_args["chaikin generations"] >= 0
            ), f"Number of generations must be positive ({self.a_args.chaikin_generations} >= 0)"
            for _ in range(self.a_args.chaikin_generations):
                vprint(" - 3D Chaikin -")
                poly = poly.Chaikin3D(self.a_args)
                vprint("Chaikin done")

        # switch the plot type
        if self.a_args.plot == "simple" or self.a_args.plot == "none":
            poly_dd = renderer.get_polyhedron_draw_data(
                poly, type_="any", alpha=self.a_args.alpha, color=self.a_args.polygon_color
            )
            if self.a_args.show_main_edges:
                main_conn_dd = renderer.get_edges_draw_data(
                    poly,
                    type_="main",
                    line_color=self.a_args.main_edge_color,
                    node_color=self.a_args.node_color,
                )
            else:
                main_conn_dd = list()
            if self.a_args.show_graphical_edges:
                graphical_conn_dd = renderer.get_edges_draw_data(
                    poly,
                    type_="graphical",
                    line_color=self.a_args.graphical_edge_color,
                    node_color=self.a_args.node_color,
                )
            else:
                graphical_conn_dd = list()
            fig = renderer.figure(poly_dd + graphical_conn_dd + main_conn_dd)
            self.save_poly(poly, fig, self.a_args.output)
            if self.a_args.plot == "simple":
                fig.show()
        elif self.a_args.plot == "full":
            fig = plotting.draw_full(renderer, poly, self.a_args)
            self.save_poly(poly, fig, self.a_args.output)
        elif self.a_args.plot == "evolution":
            fig = plotting.draw_chaikin_evolution(renderer, poly, self.a_args)
            self.save_poly(poly, fig, self.a_args.output)
        elif self.a_args.plot == "animation":
            raise NotImplementedError("Animation plot not implemetned yet")
            plotting.chaikin_animation(renderer, poly, self.a_args)
        else:
            raise ValueError(f'Unrecognized plot type "{self.a_args.plot}"')
