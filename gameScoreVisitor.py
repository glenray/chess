from chess.pgn import BaseVisitor
import pdb

'''
Called to populate gameScore text widget with the game score,
including all variations and comments.
'''
class gameScoreVisitor(BaseVisitor):
	def __init__(self, boardPane):
		self.startsVariation = False
		self.endsVariation = False
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
		if self.startsVariation:
			self.startsVariation = False
			# if board.turn == False:
			# 	self.boardPane.gameScore.insert('end', f"{board.fullmove_number}...")
			self.varStack.append(self.currentNode)
			self.currentNode = self.currentNode.parent

		if self.endsVariation:
			self.endsVariation = False
			self.currentNode = self.varStack.pop()

		self.currentNode = self.currentNode.variation(move)
		self.boardPane.nodes.append(self.currentNode)
		self.boardPane.gameScore.outputMove(board, move, self.currentNode)

	def begin_variation(self):
		self.startsVariation=True
		self.boardPane.gameScore.insert("end", "(")

	def end_variation(self):
		self.endsVariation=True
		self.boardPane.gameScore.insert("end", ") ")

	def visit_comment(self, comment):
		c = f" {{{comment}}} ".replace('\n', ' ')
		self.boardPane.gameScore.insert('end', c)

	def result(self):
		self.boardPane.gameScore.config(state='disabled')
		self.boardPane.curNode = self.boardPane.nodes[0]
		nb = self.boardPane.gui.notebook
		g=self.boardPane.game.headers
		text = f"{g['White']} v {g['Black']}"
		self.boardPane.gui.notebook.tab('current', text=text)
		self.boardPane.focus_force()
