import random
import numpy as np

class Player(object):
	def __init__(self, id, method):
		self.id = id
		self.score = 0
		self.hand = []
		self.matches = []
		self.collections = [0, 0, 0]

		self.method = method
		self.cards_number = [7, 7, 7]	# cards each player has

		self.cards_min = [{'2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0, '10': 0, 'J': 0, 'Q': 0, 'K': 0, 'A': 0} for x in range(3)]
		self.cards_max = [{'2': 3, '3': 3, '4': 3, '5': 3, '6': 3, '7': 3, '8': 3, '9': 3, '10': 3, 'J': 3, 'Q': 3, 'K': 3, 'A': 3} for x in range(3)]

		self.game_state = {'2': True, '3': True, '4': True, '5': True, '6': True, '7': True, '8': True, '9': True, '10': True, 'J': True, 'Q': True, 'K': True, 'A': True}

	def playTurn(self, players, deck, turn):

		# action: [requested Player, card value]
		if self.method == "Random":
			action = self.Random(players, deck, turn)
		elif self.method == "Greedy":
			action = self.Greedy(players, deck, turn) 
		elif self.method == "Search":
			action = self.Search(players, deck, turn)
		elif self.method == "Learning":
			action = self.Learning(players, deck, turn)

		# request card from player requestedPlayer
		print (self.id, "is requesting from player ", action['requestedPlayer'].id, "the card value of", action['card'])
		
		turn_record = {'initial_state': False, 'turn_player': self.id, 'request_player': action['requestedPlayer'].id, 'request_card': action['card'], 'cards_get': 0, 'go_fish': False, 'find_match': False}
		result = self.requestCard(action['requestedPlayer'], action['card'])
		if result == True:
			while result == True:
				turn_record['cards_get'] = turn_record['cards_get'] + 1
				result = self.requestCard(action[0], action[1])
		else:
			if len(deck.deck) > 0:
				turn_record['go_fish'] = True
				self.goFish(deck)
				print (self.id, "went fish")
			else:
				print (self.id, "passed")
		
		turn_record['find_match'] = self.findMatches()
		return turn_record

	def Random(self, players, deck, turn):
		card = random.randrange(0, len(self.hand))	# will find a random card index from player's hand to request

		requestedPlayer = -1 # will find a random player from which to requ·est a card value
		while requestedPlayer < 0 or requestedPlayer == turn:
			requestedPlayer = random.randrange(0, 3)

		action = {'requestedPlayer': players[requestedPlayer], 'card': self.hand[card].value}
		return action
	
	def Greedy(self, players, deck, turn):
		action = [players[0], 0]
		return action
	
	# MCTS with UCT
	def Search(self, players, deck, turn):
		import mcts.mcts as mcts
		import mcts.tree_policies as tree_policies
		import mcts.default_policies as default_policies
		import mcts.backups as backups
		from mcts.graph import StateNode
		import mcts.action_and_state as action_and_state

		# c = sqrt(2)
		tree_policy = tree_policies.UCB1(np.sqrt(2))
		default_policy = default_policies.random_terminal_roll_out
		backup = backups.monte_carlo

		current_state = self.set_current_state(deck)
		state = action_and_state.GOFishState(current_state)

		root_node = StateNode(None, state)

		mcts_run = mcts.MCTS(tree_policy, default_policy, backup)
		action = mcts_run(root_node)
		action = [players[0], 0]
		return action
	
	def Learning(self, players, deck, turn):
		action = [players[0], 0]
		return action

	# hand over all cards of that rank
	def requestCard(self, player2, value):
		for card in range(len(player2.hand)): 
			if player2.hand[card].value == value:
				temp = player2.hand[card]
				player2.hand[card] = player2.hand[len(player2.hand)-1]
				player2.hand.pop()
				
				self.hand.append(temp)
				print (self.id, " gets", temp.suit, temp.value)
				return True
		
		return False
	
	def set_current_state(self, deck):
		# define the current state information
		current_hand = []
		for card in self.hand:
			current_hand.append(card.value)
		current_state = {'id': self.id, 'current_player': self.id, 'player_number': 3, 'hand': current_hand, 'cards_number': self.cards_number, 'cards_in_pile': deck.length(), 'game_state': self.game_state, 'cards_max': self.cards_max, 'cards_min': self.cards_min, 'matches': self.collections}

		# set unknown cards
		current_state['unknown_cards'] = {'2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0, '10': 0, 'J': 0, 'Q': 0, 'K': 0, 'A': 0}
		for key in current_state['unknown_cards'].keys():
			if current_state['game_state'][key]:
				current_state['unknown_cards'][key] = 4
		
		for card in current_state['hand']:
			current_state['unknown_cards'][card] = current_state['unknown_cards'][card] - 1
		
		for player in range(current_state['player_number']):
			if player == current_state['id']:
				continue
			for key in current_state['cards_min'][player].keys():
				current_state['unknown_cards'][key] = current_state['unknown_cards'][key] - current_state['cards_min'][player][key]
		
		return current_state

	# draw one card from the pile
	def goFish(self, deck):
		self.hand.append(deck.deck[len(deck.deck)-1])
		deck.deck.pop()

	def drawHand(self, deck):
		for i in range(0, 7):
			self.goFish(deck)
		
		match_list = []
		matches = self.findMatches()
		while matches['find'] == True:
			match_list.append(matches['card'])
			matches = self.findMatches()
		# return the collections found in the first place
		return match_list

	# collect entire suits -> discard
	def findMatches(self): # will find matches in self's hand. 
		for i in range(len(self.hand)):
			num_of_rank = 1
			pos_of_cards = [i, 0, 0, 0]
			for j in range(len(self.hand)):
				if i == j:
					continue
				elif self.hand[i].value == self.hand[j].value:
					pos_of_cards[num_of_rank] = j
					num_of_rank = num_of_rank + 1

			if num_of_rank == 4:
				print (self.id, " gets four cards at same rank: ", self.hand[i].value)
				self.score += 1
				self.discardMatch(pos_of_cards)
				return {'find': True, 'card': self.hand[i].value}
		return {'find': False, 'card': False}

	def printHand(self):
		for i in range(0, len(self.hand)):
			print (self.hand[i].value + " of " + self.hand[i].suit)

	# discard four cards every time
	def discardMatch(self, pos_of_cards):
		self.printHand()

		self.matches.append(self.hand[pos_of_cards[0]])
		self.matches.append(self.hand[pos_of_cards[1]])
		self.matches.append(self.hand[pos_of_cards[2]])
		self.matches.append(self.hand[pos_of_cards[3]])
		print ("DISCARDING:", self.hand[pos_of_cards[0]].value, self.hand[pos_of_cards[0]].suit)
		print ("DISCARDING:", self.hand[pos_of_cards[1]].value, self.hand[pos_of_cards[1]].suit)
		print ("DISCARDING:", self.hand[pos_of_cards[2]].value, self.hand[pos_of_cards[2]].suit)
		print ("DISCARDING:", self.hand[pos_of_cards[3]].value, self.hand[pos_of_cards[3]].suit)

		# four cards -> tail
		self.hand.remove(self.hand[pos_of_cards[3]])
		self.hand.remove(self.hand[pos_of_cards[2]])
		self.hand.remove(self.hand[pos_of_cards[1]])
		self.hand.remove(self.hand[pos_of_cards[0]])

	# update the game state every turn
	def update_state(self, turn_record):
		# update initial game state
		if turn_record['initial_state'] == True:
			for each_player in range(len(turn_record['collections'])):
				for each_collection in turn_record['collections'][each_player]:
					self.cards_min[each_player][each_collection] = 0
					self.cards_max[each_player][each_collection] = 0
					self.cards_number[each_player] = self.cards_number[each_player] - 4
					self.game_state[each_collection] = False
					self.collections[each_player] = self.collections[each_player] + 1
		# update normal turn information
		else:
			# requested player has no card
			self.cards_min[turn_record['request_player']][turn_record['request_card']] = 0
			self.cards_max[turn_record['request_player']][turn_record['request_card']] = 0

			if turn_record['go_fish']:
				# pick up one card
				self.cards_number[turn_record['turn_player']] = self.cards_number[turn_record['turn_player']] + 1

				if self.cards_min[turn_record['turn_player']][turn_record['request_card']] == 0:
					self.cards_min[turn_record['turn_player']][turn_record['request_card']] = 1
			else:
				# get cards it needs
				self.cards_min[turn_record['turn_player']][turn_record['request_card']] = turn_record['cards_get'] + self.cards_min[turn_record['turn_player']][turn_record['request_card']]
				
				self.cards_number[turn_record['turn_player']] = self.cards_number[turn_record['turn_player']] + turn_record['cards_get']
				self.cards_number[turn_record['request_player']] = self.cards_number[turn_record['request_player']] - turn_record['cards_get']
			
			self.set_cards_max(turn_record)

			if turn_record['find_match']['find']:
				self.cards_number[turn_record['turn_player']] = self.cards_number[turn_record['turn_player']] - 4
				self.game_state[turn_record['find_match']['card']] = False
				self.collections[turn_record['turn_player']] = self.collections[each_player] + 1

				self.cards_min[turn_record['turn_player']][turn_record['find_match']['card']] = 0
				self.cards_max[turn_record['turn_player']][turn_record['find_match']['card']] = 0
	
	def set_cards_max(self, turn_record):
		self.cards_max[turn_record['turn_player']][turn_record['request_card']] = 4
		
		for player in range(3):
			self.cards_max[turn_record['turn_player']][turn_record['request_card']] = self.cards_max[turn_record['turn_player']][turn_record['request_card']] - self.cards_min[player][turn_record['request_card']]
		self.cards_max[turn_record['turn_player']][turn_record['request_card']] = self.cards_max[turn_record['turn_player']][turn_record['request_card']] + self.cards_min[turn_record['turn_player']][turn_record['request_card']]
		
		if self.cards_max[turn_record['turn_player']][turn_record['request_card']] == 4:
			self.cards_max[turn_record['turn_player']][turn_record['request_card']] = 3


class Deck(object):

	def __init__(self):
		values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
		suits = ['Hearts', 'Diamonds', 'Spades', 'Clubs']
		deck = []
		for suit in range(0, 4):
			for value in range(0,13):
				deck.append(Card(values[value], suits[suit]))
		self.deck = deck
		random.shuffle(self.deck)

	def printDeck(self):
		for i in range(0, len(self.deck)):
			print (self.deck[i].value + " of " + self.deck[i].suit)
	
	def length(self):
		return len(self.deck)

class Card(object):
	def __init__(self, value, suit):
		self.value = value
		self.suit = suit

def createPlayers(deck):
	player0 = Player(0, 'Search')
	player1 = Player(1, 'Random')
	player2 = Player(2, 'Random')

	collections = []
	collections.append(player0.drawHand(deck))
	collections.append(player1.drawHand(deck))
	collections.append(player2.drawHand(deck))
	players = [player0, player1, player2]

	turn_record = {'initial_state': True, 'collections': collections}
	for player in players:
		player.update_state(turn_record)

	return players

def printResults(players):
	maxScore = players[0]
	for i in range(1, len(players)):
		if players[i].score > maxScore.score:
			maxScore = players[i]
	print (maxScore.id, " wins with a score of ", maxScore.score)
	for player in players:
		print ("player ", player.id, " currently holds:")
		player.printHand()

def playGame():
	newDeck = Deck()
	players = createPlayers(newDeck)
	turn = 0

	while len(players[0].hand) > 0 and len(players[1].hand) > 0 and len(players[2].hand) > 0:
			turn_record = players[turn].playTurn(players, newDeck, turn)
			
			for player in players:
				player.update_state(turn_record)

	printResults(players)


playGame()
