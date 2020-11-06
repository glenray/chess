import pdb
# pdb.set_trace()
import chess
import chess.pgn
import copy

class gameScoreVisitor(chess.pgn.BaseVisitor):
	def __init__(self, game):
		self.output = ""
		self.startsVariation = False
		self.endsVariation = False
		self.game = game
		self.currentNode = self.game
		self.varStack = []
		self.nodes = []

	def end_headers(self):
		g=self.game.headers
		self.output += f"{g['White']} ({g['WhiteElo']}) vs. {g['Black']} ({g['BlackElo']})"
		self.output += f"\nECO: {g['ECO']}\n\n"

	def visit_header(self, tagname, tagvalue):
		pass
		# tags = ('BLACK', 'WHite', 'eco', 'event', "whiteelo", 'blackelo')
		# if tagname.casefold() in (x.casefold() for x in tags):
		# 	self.output += f"{tagname}: {tagvalue}\n"

	def visit_move(self, board, move):
		# pdb.set_trace()
		moveNo = f"{board.fullmove_number}." if board.turn else ""
		if self.endsVariation:
			self.endsVariation = False
			self.currentNode = self.varStack.pop()
			self.output+=")\n"

		if self.startsVariation:
			self.startsVariation = False
			if board.turn == False:
				moveNo = f"{board.fullmove_number}..."
			self.varStack.append(self.currentNode)
			self.currentNode = self.currentNode.parent
			self.output+="\n("

		self.currentNode = self.currentNode.variation(move)
		self.nodes.append(self.currentNode)
		self.output += f"{moveNo}{board.san(move)} "

	def begin_variation(self):
		self.startsVariation = True

	def end_variation(self):
		self.endsVariation = True

	def visit_comment(self, comment):
		c = f"{{{comment}}} ".replace('\n', ' ')
		c = '\n'+c+'\n'
		self.output += c


	def result(self):
		# pdb.set_trace()
		return self.output


if __name__ == '__main__':
	# pgnPath = "pgn/testE.pgn"
	pgnPath = "pgn/Annotated_Games.pgn"
	pgnFile = open(pgnPath, 'r')

	game = chess.pgn.read_game(pgnFile)
	v = gameScoreVisitor(game)
	output = game.accept(v)
	pdb.set_trace()
	print(output)