import pdb
# pdb.set_trace()
import chess
import chess.pgn

class gameScoreVisitor(chess.pgn.BaseVisitor):
	def __init__(self, game):
		self.output = ""
		self.startsVariation = False
		self.game = game

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
		moveNo = f"{board.fullmove_number}." if board.turn else ""
		if self.startsVariation and board.turn == False:
			self.startsVariation = False
			moveNo = f"{board.fullmove_number}..."
		self.output += f"{moveNo}{board.san(move)} "

	def begin_variation(self):
		self.startsVariation = True
		self.output+="\n("

	def end_variation(self):
		self.output+=")\n"

	def visit_comment(self, comment):
		self.output+=f"{{{comment}}} ".replace('\n', ' ')

	def result(self):
		return self.output


if __name__ == '__main__':
	# pgnPath = "pgn/testE.pgn"
	pgnPath = "pgn/Annotated_Games.pgn"
	pgnFile = open(pgnPath, 'r')

	game = chess.pgn.read_game(pgnFile)
	v = gameScoreVisitor(game)
	print(game.accept(v))
