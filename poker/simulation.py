import itertools
import random
import time
import pprint
import json


class Game:
    def __init__(self, num_players):
        self.num_players = num_players
        self.players = [Player() for _ in range(num_players)]
        self.deck = Deck()
        self.probabilities = {}

    def run_simulations(self, n):
        for _ in range(n):
            self.simulate()
        self.probabilities = {k: v for k, v in sorted(self.probabilities.items(), key=lambda prob: -prob[1].probability)}

    def simulate(self):
        self.deck.shuffle()
        self.deck.deal_hole_cards(self.players)
        self.deck.deal_community_cards()
        player_hands = [player.get_best_hand(self.deck.community_cards) for player in self.players]
        winning_hands = Hand.get_best_hand(player_hands)
        self.update_probabilities(player_hands, winning_hands)
        return

    def update_probabilities(self, player_hands, winning_hands):
        for hand in player_hands:
            prob = self.probabilities.get(str(hand.hole_cards), Probability())
            self.probabilities[str(hand.hole_cards)] = prob.update(hand in winning_hands)


class Probability:
    def __init__(self):
        self.hands_played = 0
        self.hands_won = 0
        self.probability = 0

    def __repr__(self):
        return f"{self.probability * 100:.2f}% ({self.hands_won} / {self.hands_played} hands won)"

    def update(self, won):
        if won:
            self.hands_won += 1
        self.hands_played += 1
        self.probability = self.hands_won / self.hands_played
        return self


class Player:
    def __init__(self):
        self.hole_hands = []

    def __repr__(self):
        return f"Player({self.hole_hands})"

    def get_best_hand(self, community_cards):
        assert len(self.hole_hands) == 2, 'Hole cards have not been dealt!'
        all_cards = self.hole_hands + community_cards
        hands = [Hand(cards, self.hole_hands) for cards in itertools.combinations(all_cards, 5)]
        return Hand.get_best_hand(hands)[0]


class Card:
    rank_map = {**dict({'Ace': 14, 'King': 13, 'Queen': 12, 'Jack': 11}), **dict(zip(range(2, 11), range(2, 11)))}

    def __init__(self, rank, suit):
        self.rank = rank
        self.rank_number = Card.rank_map[rank]
        self.suit = suit

    def __repr__(self):
        return f"({self.rank}, {self.suit})"

    def __eq__(self, other):
        return self.rank_number == other.rank_number and self.suit == other.suit

    def __lt__(self, other):
        return self.rank_number < other.rank_number


class Deck:
    ranks = list(range(2, 11)) + ['Ace', 'King', 'Queen', 'Jack']
    suits = ['Spades', 'Clubs', 'Hearts', 'Diamonds']

    def __init__(self):
        self.community_cards = []
        self.index = 0
        self.cards = [Card(rank, suit) for rank, suit in itertools.product(Deck.ranks, Deck.suits)]
        self.shuffle()

    def deal_hole_cards(self, players):
        for player in players:
            player.hole_hands = self.deal_cards(2)

    def deal_community_cards(self):
        self.community_cards = self.deal_cards(5)

    def deal_cards(self, num):
        assert self.index <= (52 - num), 'No cards left in deck.'
        cards = [self.cards[self.index + i] for i in range(1, num + 1)]
        self.index += num
        return cards

    def shuffle(self):
        random.shuffle(self.cards)
        self.index = 0


class Hand:
    def __init__(self, cards, hole_cards=None):
        assert len(cards) == 5
        self.cards = list(cards)
        self.cards.sort(reverse=True)
        self.hole_cards = hole_cards if hole_cards is not None else []

        self.is_straight = self._is_straight()
        self.is_flush = self._is_flush()
        self.card_freq = self._get_card_freq()
        self.score = self.get_score()

    def __repr__(self):
        return f"Hand({self.cards})"

    @staticmethod
    def get_best_hand(hands):
        max_score = max(hand.score for hand in hands)
        return [hand for hand in hands if hand.score == max_score]

    def get_score(self):
        hand_order_functions = [
            self.score_royal_flush,
            self.score_straight_flush,
            self.score_four_of_a_kind,
            self.score_full_house,
            self.score_flush,
            self.score_straight,
            self.score_three_of_a_kind,
            self.score_two_pair,
            self.score_one_pair,
            self.score_high_card
        ]
        for func in hand_order_functions:
            score = func()
            if score > 0:
                return score

    def score_royal_flush(self):
        return 10 if self.is_straight and self.is_flush and self.cards[0].rank == 'Ace' else 0

    def score_straight_flush(self):
        return 9 + self.cards[0].rank_number / 100 if self.is_straight and self.is_flush else 0

    def score_four_of_a_kind(self):
        card_rank = max(self.card_freq, key=self.card_freq.get)
        other_card_rank = set(self.card_freq.keys()).difference([card_rank]).pop()
        return 8 + card_rank / 1e2 + other_card_rank / 1e4 if 4 in self.card_freq.values() else 0

    def score_full_house(self):
        card_freqs = set(self.card_freq.values())
        if 3 in card_freqs and 2 in card_freqs:
            full_house_cards = [self._get_card_rank_with_freq(3), self._get_card_rank_with_freq(2)]
            return 7 + full_house_cards[0] / 1e2 + full_house_cards[1] / 1e4
        else:
            return 0

    def score_flush(self):
        return 6 + Hand.get_cards_score(self.cards) if self.is_flush else 0

    def score_straight(self):
        return 5 + Hand.get_cards_score(self.cards[0]) if self.is_straight else 0

    def score_three_of_a_kind(self):
        score = self._score_k_of_a_kind(3)
        return 4 + score if score > 0 else 0

    def score_two_pair(self):
        pair_ranks = [rank_number for rank_number, freq in self.card_freq.items() if freq == 2]
        if len(pair_ranks) == 0:
            return 0
        top_pair_rank = max(pair_ranks)
        other_pair_rank = min(pair_ranks)
        other_cards = [card for card in self.cards if card.rank_number not in pair_ranks]
        return 3 + top_pair_rank / 1e2 + other_pair_rank / 1e4 + Hand.get_cards_score(other_cards) / 1e4

    def score_one_pair(self):
        score = self._score_k_of_a_kind(2)
        return 2 + score if score > 0 else 0

    def score_high_card(self):
        return 1 + Hand.get_cards_score(self.cards)

    def _is_straight(self):
        for i, card in enumerate(self.cards[:4]):
            if self.cards[i].rank_number - self.cards[i + 1].rank_number != 1:
                return False
        return True

    def _is_flush(self):
        suits = set(card.suit for card in self.cards)
        return len(suits) == 1

    def _get_card_freq(self):
        card_freq = dict()
        for card in self.cards:
            card_freq[card.rank_number] = card_freq.get(card.rank_number, 0) + 1
        return card_freq

    def _get_card_rank_with_freq(self, freq):
        return list(self.card_freq.keys())[list(self.card_freq.values()).index(freq)]

    def _score_k_of_a_kind(self, k):
        card_freqs = set(self.card_freq.values())
        if k in card_freqs:
            k_of_a_kind_card = self._get_card_rank_with_freq(k)
            other_cards = [card for card in self.cards if card.rank_number != k_of_a_kind_card]
            other_card_scores = Hand.get_cards_score(other_cards)
            return self._get_card_rank_with_freq(k) / 100 + other_card_scores / 100
        else:
            return 0

    @staticmethod
    def get_cards_score(cards):
        cards = cards if isinstance(cards, list) else [cards]
        score = 0
        for i, card in enumerate(cards):
            score += card.rank_number / (100 ** (i + 1))
        return score


if __name__ == '__main__':
    game = Game(num_players=2)
    num_games = 52 * 51 * 100

    start_time = time.time()
    game.run_simulations(num_games)
    elapsed_time = time.time() - start_time

    pprint.pprint(game.probabilities)
    print(game.probabilities)
    print(f"Took {elapsed_time:.2f}s for {num_games} simulations")
