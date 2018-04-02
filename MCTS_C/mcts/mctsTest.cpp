#include "mctsTest.h"

namespace mcts_skat {

	bool is_bigger(int Card1, int Card2, int trump) {
		// Card1 is Jack
		if (Card1 % 10 == 0) {
			if (Card2 % 10 == 0 && Card2 < Card1)
				return false;
			else
				return true;
		}
		// Card1 is Trump without Jack
		else if (Card1 / 10 == trump) {
			if (Card2 % 10 == 0 || (Card2 / 10 == trump && Card2 < Card1))
				return false;
			else
				return true;
		}
		// Card1 is not Trump
		else {
			if (Card2 % 10 == 0 || Card2 / 10 == trump || (Card1 / 10 == Card2 / 10 && Card2 < Card1))
				return false;
			else
				return true;
		}
	}

	int turn_winner(int* currentState, int trump) {
		int turnWinner = -1;

		if (is_bigger(currentState[0], currentState[1], trump)) {
			if (is_bigger(currentState[0], currentState[2], trump))
				turnWinner = 0;
			else
				turnWinner = 2;
		}
		else {
			if (is_bigger(currentState[1], currentState[2], trump))
				turnWinner = 1;
			else
				turnWinner = 2;
		}

		return turnWinner;
	}

	int card_value(int Card) {
		int value = 0;
		switch (Card % 10) {
		case 0:		// Jack
			value = 2;
			break;
		case 1:		// Ace
			value = 11;
			break;
		case 2:		// 10
			value = 10;
			break;
		case 3:		// King
			value = 4;
			break;
		case 4:		// Queen
			value = 3;
			break;
		default:	// 7,8,9 without value
			break;
		}
		return value;
	}
}