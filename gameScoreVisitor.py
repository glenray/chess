from chess.pgn import BaseVisitor
import pdb

'''
Called to populate gameScore text widget with the game score,
including all variations and comments.
'''
class gameScoreVisitor(BaseVisitor):
	def __init__(self, boardPane):
		self.boardPane = boardPane
		self.currentNode = self.boardPane.game
		# at the start of a new variation, the current node is pushed
		# to the varStack and popped off when the new variation finishes.
		self.varStack = []
		# the first node is the root, i.e. start position
		self.boardPane.nodes = [self.currentNode]

	def end_headers(self):
		self.boardPane.gameScore.outputHeaders()

	def visit_move(self, board, move):
		self.currentNode = self.currentNode.variation(move)
		self.boardPane.nodes.append(self.currentNode)
		self.boardPane.gameScore.outputMove(move, self.currentNode)

	def begin_variation(self):
		self.varStack.append(self.currentNode)
		self.currentNode = self.currentNode.parent

	def end_variation(self):
		self.boardPane.gameScore.config(state='normal')
		self.boardPane.gameScore.insert('end', ') ')
		self.boardPane.gameScore.config(state='disabled')
		self.currentNode = self.varStack.pop()

	def result(self):
		self.boardPane.gameScore.config(state='disabled')
		self.boardPane.curNode = self.boardPane.nodes[0]
		nb = self.boardPane.gui.notebook
		g=self.boardPane.game.headers
		text = f"{g['White']} v {g['Black']}"
		self.boardPane.gui.notebook.tab('current', text=text)
		self.boardPane.focus_force()
