from tkinter import Canvas

'''
Subclass of tkinter Canvas widget that maintains square aspect ratio
6/7/2020: Glen Pritchard

Sets the height and width of the canvas to its parent window/frame's shortest dimension.
'''
class sqCanvas(Canvas):
	def __init__(self,parent,**kwargs):
		Canvas.__init__(self,parent,**kwargs)
		self.bind("<Configure>", self.on_resize)

	# resize the canvas as a square based on shortest dimension of master widget
	def on_resize(self, e):
		side = min(self.master.winfo_width(), self.master.winfo_height())
		self.config(width=side, height=side)