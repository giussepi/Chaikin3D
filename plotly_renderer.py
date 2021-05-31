# Polygon rendering
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from polygon import Polygon

DO_CHAIKIN = True

def gen_random_color():
	s = '#'
	import random
	choices = '0123456789abcdef'
	for _ in range(6):
		s += random.choice(choices)
	return s

class Renderer:
	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs

		self.active_subplot = False
		self.subplot_fig = None
		self.subplot_row_index = 0
		self.subplot_row_limit = 0
		self.subplot_col_index = 0
		self.subplot_col_limit = 0

	def draw(self, data : list):
		fig = go.Figure(data, *self.args, **self.kwargs)
		fig.show()

	def init_subplots(self, rows : int, cols : int, *args, **kwargs) -> None:
		assert not self.active_subplot # cannot have two subplots at a time
		assert rows > 0 # >= 1
		assert cols > 0 # >= 1
		self.active_subplot = True
		specs = [[{'type': 'scene'}] * cols] * rows
		self.subplot_fig = make_subplots(rows = rows, cols = cols, specs = specs, *args, **kwargs)
		self.subplot_row_index = 1
		self.subplot_row_limit = rows
		self.subplot_col_index = 1
		self.subplot_col_limit = cols

	def fill_subplot(self, data : list, *args, **kwargs):
		assert self.active_subplot # make sure we are actually drawing subplots
		self.subplot_fig.add_trace(
			data,
			row = self.subplot_row_index,
			col = self.subplot_col_index,
			*args,
			**kwargs
		)
		# go to the next row ol column
		self.next_subplot()

	def add_to_subplot(self, data : list, function = None, custom_row : int = -1, custom_col : int = -1, *args, **kwargs):
		assert self.active_subplot # make sure we are actually drawing subplots
		# default function if None
		if function == None:
			function = self.subplot_fig.add_trace

		# if you customize one, please customize the other too
		if custom_row != -1: assert custom_col != -1
		elif custom_col != -1: assert custom_row != -1

		function(
			data,
			row = self.subplot_row_index if custom_row == -1 else custom_row,
			col = self.subplot_col_index if custom_col == -1 else custom_col,
			*args,
			**kwargs
		)

	def next_subplot(self) -> None:
		assert self.active_subplot
		if self.subplot_col_index == self.subplot_col_limit:
			self.subplot_col_index = 1
			self.subplot_row_index += 1
			if self.subplot_row_index > self.subplot_row_limit:
				self.active_subplot = False
				print('subplot filled')
			return
		# no limit reached
		self.subplot_col_index += 1

	def draw_subplots(self):
		self.subplot_fig.show()
		# don't reset figure on purpose (why do it ? could be used later by user)
		self.active_subplot = False
		self.subplot_row_index = 0
		self.subplot_row_limit = 0
		self.subplot_col_index = 0
		self.subplot_col_limit = 0

	def get_polygon_draw_data(self, polygon : Polygon, type_ : str = 'any', alpha : float = 0.8, draw_text : bool = False, color : str = 'lightblue') -> list[go.Mesh3d]:
		vertex_list = []
		vertex_index_list = []
		for triplet in polygon._hash_iter_triplets(type_):
			index_list = []
			for vertex in triplet:
				if vertex not in vertex_list:
					vertex_list.append(vertex)
					index_list.append(len(vertex_list) - 1)
				else:
					index_list.append(vertex_list.index(vertex))
			vertex_index_list.append(index_list)

		if not vertex_list and not vertex_index_list:
			print('No polygon data')
			return []

		X, Y, Z = list(zip(*vertex_list))
		I, J, K = list(zip(*vertex_index_list))
		return [go.Mesh3d(
			x=X, y=Y, z=Z,
			color=gen_random_color() if color == 'random' else color,
			i=I,
			j=J,
			k=K,
			opacity=alpha
		)]

	def draw_polygon(self, polygon : Polygon, alpha : float = 0.8, draw_text : bool = True) -> None:
		self.draw(data=self.get_polygon_draw_data(polygon, alpha, draw_text))

	def get_connections_draw_data(self, polygon : Polygon, type_ : str = 'any', color : str = 'lightblue', width : int = 2) -> list[go.Scatter3d]:
		figure_data : list[go.Scatter3d] = []
		for connection in polygon.get_connections(type_):
			A, B = connection.A.coords, connection.B.coords
			figure_data.append(go.Scatter3d(
				x = [A[0], B[0]],
				y = [A[1], B[1]],
				z = [A[2], B[2]],
				marker={
					'size': 2,
					'color': gen_random_color() if color == 'random' else color
				},
				line={
					'color': gen_random_color() if color == 'random' else color,
					'width': 2,
					'dash': 'solid'
				}
			))
		return figure_data

	def draw_connections(self, polygon : Polygon, type_ : str = 'any', color : str = 'lightblue', width : int = 2) -> None:
		self.draw(data=self.get_connections_draw_data(polygon, type_, color, width))


'''
fig = go.Figure(
	data=[
		go.Scatter3d(
			x = [0,1,2],
			y = [0,2,1],
			z = [1,1,1],
			line=dict(
				color='darkblue',
				width=2
			)
		),
		go.Scatter3d(
			x = [2,1,2],
			y = [2,1,0],
			z = [0,2,0],
			line=dict(
				color='darkblue',
				width=2
			)
		)
	]
)


fig.show()
'''
