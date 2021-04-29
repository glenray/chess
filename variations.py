import tkinter as tk

class Variations(tk.Listbox):
	def __init__(self, parent, boardPane):
		self.boardPane = boardPane
		tk.Listbox.__init__(self, parent)
		# exportselection prevents selecting from the list box in one board pane from deselecting the others. https://github.com/PySimpleGUI/PySimpleGUI/issues/1158
		self.configure(width=20, exportselection=False)
		# prevent variations from taking focus and blocking keyboard events
		self.bind('<FocusIn>', lambda e: self.boardPane.focus())

	# select a variation in the variations listbox using up/down arrows
	def selectVariation(self, e):
		variationsLength = len(self.get(0, tk.END))
		# quit if there are no variations, i.e. the end of a variation
		if variationsLength == 0: return
		curIdx = self.curselection()[0]
		isBottom = curIdx == variationsLength-1
		isTop = curIdx == 0
		# Down arrow
		if e.keycode == 40:
			if isBottom: return
			self.selection_clear(0, tk.END)
			curIdx = curIdx+1
			self.selection_set(curIdx)
		# Up arrow
		elif e.keycode == 38:
			if isTop: return
			self.selection_clear(0, tk.END)
			curIdx = curIdx-1
			self.selection_set(curIdx)

	# insert current variations into the variation list box
	def printVariations(self):
		self.delete(0, tk.END)
		for var in self.boardPane.curNode.variations:
			b=var.parent.board()
			moveNo = b.fullmove_number if b.turn==True else f'{b.fullmove_number}...'
			self.insert(self.boardPane.curNode.variations.index(var), f"{moveNo} {var.san()}")
		self.selection_set(0)

