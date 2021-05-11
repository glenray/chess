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
		insertPoint = self._getInsertPoint()
		self.boardPane.gameScore.outputMove(move, self.currentNode, insertPoint)

	def _getInsertPoint(self):
		'''
		Moves in the mainline go at the end of the text widget.
		But, moves inside variations go inside closing parens intead.
		Each level of sub variation adds 2 characters [' )']
		Plus one more char for the '\n' at the end of the line.
		Moves that start a variation should be offset by one level up.
		'''
		varDepth = len(self.varStack)
		insertPoint = f'end-{varDepth*2+1} chars' if varDepth>0 and not self.currentNode.starts_variation() else 'end'
		if varDepth>1 and self.currentNode.starts_variation():
			insertPoint = f'end-{(varDepth-1)*2+1} chars'
		return insertPoint

	def begin_variation(self):
		self.varStack.append(self.currentNode)
		self.currentNode = self.currentNode.parent

	def end_variation(self):
		self.currentNode = self.varStack.pop()

	def result(self):
		self.boardPane.gameScore.tag_remove('curMove', '0.0', 'end')
		self.boardPane.curNode = self.boardPane.nodes[0]
		nb = self.boardPane.gui.notebook
		g=self.boardPane.game.headers
		text = f"{g['White']} v {g['Black']}"
		self.boardPane.gui.notebook.tab('current', text=text)
		self.boardPane.focus_force()
