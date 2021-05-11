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
		self.insertPoint = 'end'
		# the first node is the root, i.e. start position
		self.boardPane.nodes = [self.currentNode]

	def end_headers(self):
		self.boardPane.gameScore.outputHeaders()

	def visit_move(self, board, move):
		self.currentNode = self.currentNode.variation(move)
		self.boardPane.nodes.append(self.currentNode)
		# moves inside variations need to go inside closing parens intead of at end
		# for each level of sub variation we offset 2 characters for the ' )' plus
		# one more char for the '\n' at the end of the line.
		varDepth = len(self.varStack)
		self.insertPoint = f'end-{varDepth*2+1} chars' if varDepth>0 and not self.currentNode.starts_variation() else 'end'
		# starting variation needs to be one level of depth
		if varDepth>1 and self.currentNode.starts_variation():
			self.insertPoint = f'end-{(varDepth-1)*2+1} chars'
		self.boardPane.gameScore.outputMove(move, self.currentNode, self.insertPoint)

	def begin_variation(self):
		self.varStack.append(self.currentNode)
		self.currentNode = self.currentNode.parent

	def end_variation(self):
		self.currentNode = self.varStack.pop()

	def result(self):
		self.boardPane.gameScore.config(state='disabled')
		self.boardPane.curNode = self.boardPane.nodes[0]
		nb = self.boardPane.gui.notebook
		g=self.boardPane.game.headers
		text = f"{g['White']} v {g['Black']}"
		self.boardPane.gui.notebook.tab('current', text=text)
		self.boardPane.focus_force()
