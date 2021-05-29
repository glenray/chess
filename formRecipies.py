recipies = {
	'getGamesBtwPlayers':{
		'title'  : "Search for Games\nBetween Players",
		'params' : {'p1' : 'Player 1', 'p2' : 'Player 2'},
		'sql'	: '''SELECT 
		games.rowid as gameId,
		games.game as pgnString,
		lists.value as source
		FROM games
		JOIN lists ON lists.rowid = games.source 
		WHERE games.rowid
		IN (
			SELECT gameID
			FROM related
			join lists ON lists.rowid = related.listID
			WHERE 
				(related.value GLOB :p1 and lists.value = 'Black') or
				(related.value GLOB :p1 and lists.value = 'White')
		INTERSECT
			SELECT gameID
			FROM related
			join lists ON lists.rowid=related.listID
			WHERE
				(related.value GLOB :p2 and lists.value = 'Black') or
				(related.value GLOB :p2 and lists.value = 'White')
		)'''
	},
	'getPlayerGames': {
		'title'	: "Search for a Player",
		'params'	: {'p1' : "Player"},
		'sql'	: '''SELECT 
		games.rowid as gameId,
		games.game as pgnString,
		lists.value as source
		FROM games
		JOIN lists ON lists.rowid = games.source 
		WHERE games.rowid
		IN (
			SELECT gameID
			FROM related
			join lists ON lists.rowid = related.listID
			WHERE 
				(related.value GLOB :p1 and lists.value = 'Black') or
				(related.value GLOB :p1 and lists.value = 'White')
		)'''
	}
}
