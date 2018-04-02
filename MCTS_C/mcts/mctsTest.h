#pragma once
#include "ofxMSAmcts.h"
using namespace msa::mcts;

namespace mcts_skat {

	bool is_bigger(int Card1, int Card2, int trump);

	int turn_winner(int* currentState, int trump);

	int card_value(int Card);

	// play card action
	struct Action {
		int suit;
		int value;
	};

	struct input_state_info {
		bool cards[4][8];
		bool gameState[4][8];
		int player_id;
		int declarer_id;
		int current_suit;
		int win_value[3];
		int trump_suit;
		int play_sequence[3];
		int current_player;
		int turn_count;
		bool player_not_have[3][4];
	};

	class State {
	public:
		//--------------------------------------------------------------
		// MUST HAVE METHODS (INTERFACE)

		State() { }

		State(input_state_info input_state) {
			this_state = input_state;
		}

		State(const State& other) {
			this_state = other.this_state;
		}

		// default constructors will do
		// copy and assignment operators should perform a DEEP clone of the given state
		//    State(const State& other);
		//    State& operator = (const State& other);


		// whether or not this state is terminal (reached end)
		bool is_terminal() const {
			bool card_left = false;
			int two_skat_cards = 0;

			for(int suit = 0; suit < 4 ; suit++)
				for (int card = 0; card < 8; card++) {
					if (this_state.cards[suit][card])
						card_left = true;
					if (this_state.gameState[suit][card])
						two_skat_cards++;
				}

			// check if all the cards are played
			if (card_left || (two_skat_cards > 2 && this_state.player_id != this_state.declarer_id) || (two_skat_cards > 0 && this_state.player_id == this_state.declarer_id))
				return false;
			else
				return true;
			
		}

		//  agent id (zero-based) for agent who is about to make a decision
		int agent_id() const {
			return this_state.current_player;
		}

		// apply action to state
		void apply_action(const Action& action) {
			this_state.gameState[action.suit][action.value] = false;
			this_state.cards[action.suit][action.value] = false;

			this_state.play_sequence[this_state.turn_count] = action.suit * 10 + action.value;

			if (this_state.turn_count == 0) {
				if (action.suit == this_state.trump_suit || action.value == 0)
					this_state.current_suit = this_state.trump_suit;
				else
					this_state.current_suit = action.suit;
			}

			this_state.turn_count = (this_state.turn_count + 1) % 3;
			this_state.current_player = (this_state.current_player + 1) % 3;

			// new turn, calculate the previous turn
			if (this_state.turn_count == 0) {
				int winner = turn_winner(this_state.play_sequence, this_state.trump_suit);
				
				// set winner the first player for next turn
				this_state.current_player = (winner + this_state.current_player) % 3;

				// get all three cards
				this_state.win_value[this_state.current_player] += card_value(this_state.play_sequence[0]);
				this_state.win_value[this_state.current_player] += card_value(this_state.play_sequence[1]);
				this_state.win_value[this_state.current_player] += card_value(this_state.play_sequence[2]);
			}
		}


		// return possible actions from this state
		void get_actions(std::vector<Action>& actions) const {
			actions.resize(0);
			// int action_number = 0;

			// first player
			if (this_state.turn_count == 0) {
				if (this_state.current_player == this_state.player_id) {
					for (int suit = 0; suit < 4; suit++) {
						for (int value = 0; value < 8; value++) {
							if (this_state.cards[suit][value] == true) {
								Action* action = new Action();
								action->suit = suit;
								action->value = value;

								actions.push_back(*action);
							}
						}
					}
				}
				else {
					for (int suit = 0; suit < 4; suit++) {
						for (int value = 0; value < 8; value++) {
							// ***
							if (this_state.player_not_have[this_state.current_player][suit] == true)
								continue;
							if (this_state.gameState[suit][value] == true) {
								Action* action = new Action();
								action->suit = suit;
								action->value = value;

								actions.push_back(*action);
							}
						}
					}
				}
			}
			// need to follow the suit
			else {
				if (this_state.current_player == this_state.player_id) {
					// add all trumps
					for (int value = 0; value < 8; value++) {
						if (this_state.cards[this_state.trump_suit][value] == true) {
							Action* action = new Action();
							action->suit = this_state.trump_suit;
							action->value = value;

							actions.push_back(*action);
						}
					}

					for (int suit = 0; suit < 4; suit++) {
						if (suit == this_state.trump_suit || this_state.cards[suit][0] == false)
							continue;
						else {
							Action* action = new Action();
							action->suit = suit;
							action->value = 0;

							actions.push_back(*action);
						}
					}

					int trump_action_number = actions.size();

					// add current suit cards
					if (this_state.current_suit != this_state.trump_suit) {
						for (int value = 0; value < 8; value++) {
							if (this_state.cards[this_state.current_suit][value] == true && value != 0) {
								Action* action = new Action();
								action->suit = this_state.current_suit;
								action->value = value;

								actions.push_back(*action);
							}
						}
					}

					// no current suit card
					if ((this_state.current_suit != this_state.trump_suit && actions.size() == trump_action_number)
						|| actions.size() == 0) {
						for (int suit = 0; suit < 4; suit++) {
							for (int value = 0; value < 8; value++) {
								if (this_state.cards[suit][value] == true) {
									Action* action = new Action();
									action->suit = suit;
									action->value = value;

									actions.push_back(*action);
								}
							}
						}
					}
				}
				else {
					// add all trumps
					// ***
					if (this_state.player_not_have[this_state.current_player][this_state.trump_suit] == false) {
						for (int value = 0; value < 8; value++) {
							if (this_state.gameState[this_state.trump_suit][value] == true) {
								Action* action = new Action();
								action->suit = this_state.trump_suit;
								action->value = value;

								actions.push_back(*action);
							}
						}

						for (int suit = 0; suit < 4; suit++) {
							if (suit == this_state.trump_suit || this_state.gameState[suit][0] == false)
								continue;
							else {
								Action* action = new Action();
								action->suit = suit;
								action->value = 0;

								actions.push_back(*action);
							}
						}
					}		

					int trump_action_number = actions.size();

					// add current suit cards
					// ***
					if (this_state.current_suit != this_state.trump_suit && this_state.player_not_have[this_state.current_player][this_state.current_suit] == false) {
						for (int value = 0; value < 8; value++) {
							if (this_state.gameState[this_state.current_suit][value] == true && value != 0) {
								Action* action = new Action();
								action->suit = this_state.current_suit;
								action->value = value;

								actions.push_back(*action);
							}
						}
					}

					// no current suit card
					if (actions.size() == trump_action_number || actions.size() == 0) {
						for (int suit = 0; suit < 4; suit++) {
							for (int value = 0; value < 8; value++) {
								// ***
								if (this_state.player_not_have[this_state.current_player][suit] == true || suit == this_state.trump_suit)
									continue;
								if (this_state.gameState[suit][value] == true) {
									Action* action = new Action();
									action->suit = suit;
									action->value = value;

									actions.push_back(*action);
								}
							}
						}
					}
				}
			}

			// impossible game state
			if (actions.size() == 0) {

			}
			//actions.resize(action_number);
		}

		// get a random action, return false if no actions found
		bool get_random_action(Action& action) const {
			std::vector<Action> actions;			// possible actions from this state
			get_actions(actions);

			if (actions.size() == 0)
				return false;

			int random_action = rand() % actions.size();
			action = actions[random_action];

			return true;
		}


		// evaluate this state and return a vector of rewards (for each agent)
		const vector<float> evaluate() const {
			vector<float> rewards(3);

			// invalid state
			if (this_state.win_value[0] + this_state.win_value[1] + this_state.win_value[2] < 120) {
				for (int i = 0; i < 3; i++)
					rewards[i] = 0;
			}
			// normal state
			else {
				if (this_state.win_value[this_state.declarer_id] > 61)
					for (int i = 0; i < 3; i++) {
						if (i == this_state.declarer_id)
							rewards[i] = 1;
						else
							rewards[i] = 0;
					}
				else
					for (int i = 0; i < 3; i++) {
						if (i == this_state.declarer_id)
							rewards[i] = 0;
						else
							rewards[i] = 1;
					}
			}
			return rewards;
		}

	private:
		input_state_info this_state;
	};

}