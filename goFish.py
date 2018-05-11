import random
import numpy as np

import mcts.mcts as mcts
import mcts.tree_policies as tree_policies
import mcts.default_policies as default_policies
import mcts.backups as backups
from mcts.graph import StateNode
import mcts.action_and_state as action_and_state

import random
import operator as op
from functools import reduce

# Learning
from keras.models import Sequential, load_model
from keras.layers import LSTM, TimeDistributed, Dense, Activation
from keras.optimizers import Adam

from pathlib import Path
import h5py

# combination formula
def ncr(n, r):
    r = min(r, n-r)
    numer = reduce(op.mul, range(n, n-r, -1), 1)
    denom = reduce(op.mul, range(1, r+1), 1)
    return numer//denom

class RNN(object):
	def __init__(self, 
		BATCH_START = 0,
		TIME_STEPS = 20,
		BATCH_SIZE = 50,
		INPUT_SIZE = (71,),
		OUTPUT_SIZE = 71,
		CELL_SIZE = 20,
		LR = 0.006):
		
		model_HDF5 = Path('./RNN_model.h5')
		# if exist, load the model
		if model_HDF5.is_file():
			self.model = load_model('RNN_model.h5')
		# else create a new RNN model
		else:
			self.model = Sequential()
			# build a LSTM RNN
			self.model.add(LSTM(
				OUTPUT_SIZE,
				input_shape=INPUT_SIZE,       # Or: input_dim=INPUT_SIZE, input_length=TIME_STEPS,
				output_dim=CELL_SIZE,
				return_sequences=True,      # True: output at all steps. False: output as last step.
			))
			# add output layer
			self.model.add(TimeDistributed(Dense(OUTPUT_SIZE)))
			self.model.add(Activation('softmax'))

			adam = Adam(LR)
			self.model.compile(optimizer = adam, loss = 'mean_squared_error')

	def train(self, X_batch, Y_batch, n_batch):
		self.model.fit(X_batch, Y_batch, epochs = 1, batch_size = n_batch, shuffle = False, verbose = 2)
	
	def predict(self, X_batch, n_batch):
		Y_batch = self.model.predict(X_batch, batch_size = n_batch)
		predict = Y_batch[-1]
		return predict

	def save(self):
		self.model.save('RNN_model.h5')

class Player(object):
	def __init__(self, id, method):
		self.id = id
		self.score = 0
		self.hand = []
		self.matches = []
		self.collections = [0, 0, 0]

		self.method = method
		self.RNN_model = None
		if self.method == 'Learning':
			self.RNN_model = RNN()

		self.cards_number = [7, 7, 7]	# cards each player has

		self.cards_min = [{'2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0, '10': 0, 'J': 0, 'Q': 0, 'K': 0, 'A': 0} for x in range(3)]
		self.cards_max = [{'2': 3, '3': 3, '4': 3, '5': 3, '6': 3, '7': 3, '8': 3, '9': 3, '10': 3, 'J': 3, 'Q': 3, 'K': 3, 'A': 3} for x in range(3)]

		self.game_state = {'2': True, '3': True, '4': True, '5': True, '6': True, '7': True, '8': True, '9': True, '10': True, 'J': True, 'Q': True, 'K': True, 'A': True}

		self.history = []

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
			count = 0
			while result == True and count < 3:
				turn_record['cards_get'] = turn_record['cards_get'] + 1
				count = count + 1
				result = self.requestCard(action['requestedPlayer'], action['card'])
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
		evaluation = {}
		self_card = {'2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0, '10': 0, 'J': 0, 'Q': 0, 'K': 0, 'A': 0}
		for card in self.hand:
			self_card[card.value] = self_card[card.value] + 1
		
		current_state = self.set_current_state(deck)
		all_unknown_cards = 0
		for card in current_state['unknown_cards'].keys():
			all_unknown_cards = all_unknown_cards + current_state['unknown_cards'][card]


		for card in self_card.keys():
			if self_card[card] == 0:
				continue
			
			players_prob = [0, 0, 0]
			for player in range(3):
				if player == self.id:
					continue
				
				player_unknown_cards = current_state['cards_number'][player]
				for card_one_have in current_state['cards_min'][player].keys():
					player_unknown_cards = player_unknown_cards - current_state['cards_min'][player][card_one_have]
				
				# possible to get collection
				if self.cards_max[player][card] + self_card[card] >= 4:
					num_need_guess = self.cards_max[player][card] - self.cards_min[player][card]

					players_prob[player] = (ncr(current_state['unknown_cards'][card], num_need_guess) * ncr(all_unknown_cards - current_state['unknown_cards'][card], player_unknown_cards - num_need_guess)) / ncr(all_unknown_cards, player_unknown_cards)
				else:
					players_prob[player] = 0

			evaluation[card] = 	players_prob.copy()	
		
		max_prob = 0
		max_card = []
		for card in evaluation.keys():
			max_individual = 0
			for individual in evaluation[card]:
				if individual > max_individual:
					max_individual = individual
			
			if max_individual > max_prob:
				max_prob = max_individual
				max_card = [card]
			elif max_individual == max_prob:
				max_card.append(card)
		
		roll_card = random.randint(0, len(max_card) - 1)
		player_option = []
		max_individual = 0
		for player in range(3):
			if evaluation[max_card[roll_card]][player] > max_individual:
				max_individual = evaluation[max_card[roll_card]][player]
				player_option = [player]
			elif evaluation[max_card[roll_card]][player] == max_individual:
				player_option.append(player)
		
		roll_player = random.randint(0, len(player_option) - 1)

		action = {'requestedPlayer': players[player_option[roll_player]], 'card': max_card[roll_card]}
		return action
	
	# MCTS with UCT
	def Search(self, players, deck, turn):
		# c = sqrt(2)
		tree_policy = tree_policies.UCB1(np.sqrt(2))
		# default_policy = default_policies.random_terminal_roll_out
		default_policy = default_policies.RandomKStepRollOut(50)
		backup = backups.monte_carlo

		current_state = self.set_current_state(deck)
		state = action_and_state.GOFishState(current_state)

		root_node = StateNode(None, state)

		mcts_run = mcts.MCTS(tree_policy, default_policy, backup)
		action = mcts_run(root_node, n = 800)
		action = {'requestedPlayer': players[action[0]], 'card': action[1]}
		return action
	
	def Learning(self, players, deck, turn):
		
		action = {'requestedPlayer': players[0], 'card': 0}
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
				collection = {'find': True, 'card': self.hand[i].value}
				self.score += 1
				self.discardMatch(pos_of_cards)
				return collection
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
	def update_state(self, turn_record, score = None):
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
			# record history
			player = [0 for x in range(3)]
			player[turn_record['turn_player']] = 1

			action = [0 for x in range(39)]
			card_sequence = list(self.game_state.keys()).index(turn_record['request_card'])
			action[turn_record['request_player'] * 13 + card_sequence] = 1
			
			game_state = []
			for card in self.game_state:
				if card == True:
					game_state.append(1)
				else:
					game_state.append(0)
			
			self_cards = {'2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0, '10': 0, 'J': 0, 'Q': 0, 'K': 0, 'A': 0}
			for each in self.hand:
				self_cards[each.value] += 1
			self_cards = list(self_cards.values())

			self.history.append(player + action + score + game_state + self_cards)
			print(self.history, len(self.history[-1]))

			# requested player has no card
			self.cards_min[turn_record['request_player']][turn_record['request_card']] = 0
			self.cards_max[turn_record['request_player']][turn_record['request_card']] = 0
			
			if self.cards_min[turn_record['turn_player']][turn_record['request_card']] == 0:
				self.cards_min[turn_record['turn_player']][turn_record['request_card']] = 1
			
			if turn_record['go_fish']:
				# pick up one card
				self.cards_number[turn_record['turn_player']] = self.cards_number[turn_record['turn_player']] + 1
				for card in self.cards_max[turn_record['turn_player']].keys():
					if self.cards_max[turn_record['turn_player']][card] < 3:
						self.cards_max[turn_record['turn_player']][card] = self.cards_max[turn_record['turn_player']][card] + 1
			else:
				# get cards it needs
				self.cards_min[turn_record['turn_player']][turn_record['request_card']] = turn_record['cards_get'] + self.cards_min[turn_record['turn_player']][turn_record['request_card']]
				
				self.cards_number[turn_record['turn_player']] = self.cards_number[turn_record['turn_player']] + turn_record['cards_get']
				self.cards_number[turn_record['request_player']] = self.cards_number[turn_record['request_player']] - turn_record['cards_get']
			
			self.set_cards_max(turn_record)

			if turn_record['find_match']['find']:
				self.cards_number[turn_record['turn_player']] = self.cards_number[turn_record['turn_player']] - 4
				self.game_state[turn_record['find_match']['card']] = False
				self.collections[turn_record['turn_player']] = self.collections[turn_record['turn_player']] + 1

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

def createPlayers(deck, player_type = ['Random', 'Random', 'Random']):
	player0 = Player(0, player_type[0])
	player1 = Player(1, player_type[1])
	player2 = Player(2, player_type[2])

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
	winner_number = 1
	for i in range(1, len(players)):
		if players[i].score > maxScore.score:
			maxScore = players[i]
			winner_number = 1
		elif players[i].score == maxScore.score:
			winner_number += winner_number
	if winner_number == 1:
		print (maxScore.id, " wins with a score of ", maxScore.score)
		for player in players:
			print ("player ", player.id, " scores:")
			# player.printHand()
			print(player.score)
	else:
		print('multiple winners')
		return -1
	return maxScore.id

def playGame(player_type = ['Random', 'Random', 'Random']):
	newDeck = Deck()
	players = createPlayers(newDeck, player_type)
	turn = 0

	while len(players[0].hand) > 0 and len(players[1].hand) > 0 and len(players[2].hand) > 0:
			turn_record = players[turn].playTurn(players, newDeck, turn)
			
			for player in players:
				player.update_state(turn_record, [players[0].score, players[1].score, players[2].score])
			
			turn = (turn + 1) % len(players)

	winner = printResults(players)
	return winner

def experiment(player_type = ['Random', 'Random', 'Random'], n = 100):
	winning_rate = [0, 0, 0]
	
	for turn in range(n):
		winner_id = playGame(player_type)
		if winner_id != -1:
			winning_rate[winner_id] += 1
	
	return winning_rate

player_type = ['Greedy', 'Greedy', 'Greedy']
turn = 500
game_data = experiment(player_type, turn)

with open('C:/Users/ljsPC/Desktop/go_fish_data2.txt', 'w') as experiment_data:
	print('game winning rate: ', game_data)
	data = {player_type[0]: game_data[0], player_type[1]: game_data[1] + game_data[2]}
	experiment_data.writelines(str(turn))
	experiment_data.writelines(str(data))
