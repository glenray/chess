import tkinter as tk
import tkinter.ttk as ttk

class dbPane (tk.PanedWindow):
	def __init__(self, parent, pgnFile=None):
		tk.PanedWindow.__init__(self, parent.notebook)
		self.config(orient="vertical", sashwidth=10, sashrelief='raised')
		self.gui = parent
		self.setup()

	def setup(self):
		# Insert pane into the parent notebook
		self.frame1 = tk.Frame(self, bg='red')
		self.frame2 = tk.Frame(self, bg='blue')
		self.text1 = tk.Text(self.frame1, wrap= tk.WORD, padx=10, pady=10, font=("Tahoma", 14))
		self.text2 = tk.Text(self.frame2, wrap= tk.WORD, padx=10, pady=10, font=("Tahoma", 14))

		self.gui.notebook.insert('end', self, text="1 DB")
		self.gui.notebook.select(self.gui.notebook.index('end')-1)
		
		self.add(self.frame1, stretch='always')
		self.add(self.frame2, stretch='always')

		self.text1.pack()
		self.text2.pack()