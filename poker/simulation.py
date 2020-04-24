import itertools
import random
import time
import pprint
import os
import multiprocessing as mp
import collections
import pandas as pd
from typing import List


class Game:
    def __init__(self, num_players):
        self.num_players = num_players
        self.players = [Player() for _ in range(num_players)]
        self.deck = Deck()
        self.probabilities = {}

    def run_simulations(self, n, result_queue):
        for i in range(n):
            if i % 1e5 == 0:
                print(f"Running {i:,} / {n:,} simulations for {self.num_players} players.")
            self.simulate()
        result_queue.put(self)

    def simulate(self):
        self.deck.shuffle()
        self.deck.deal_hole_cards(self.players)
        self.deck.deal_community_cards()
        player_hands = [player.get_hand(self.deck.community_cards) for player in self.players]
        winning_hands = self.get_winning_hands(player_hands)
        self.update_probabilities(player_hands, winning_hands)

    def print_probabilities(self):
        print({k: v for k, v in sorted(self.probabilities.items(), key=lambda prob: -prob[1].probability)})

    @staticmethod
    def get_winning_hands(hands):
        max_score = max(hand.score for hand in hands)
        winning_hands = [hand for hand in hands if hand.score == max_score]
        return winning_hands

    def update_probabilities(self, player_hands, winning_hands):
        for hand in player_hands:
            prob = self.probabilities.get(str(hand.hole_cards), Probability())
            self.probabilities[str(hand.hole_cards)] = prob.update(hand in winning_hands)

    def store_probabilities(self):
        path = os.path.join(os.path.dirname(__file__), '../data/probabilities.csv')
        orig_df = pd.read_csv(path)
        prob_df = pd.DataFrame(
            [dict(players=self.num_players, hand=hand, new_won=prob.hands_won, new_played=prob.hands_played)
             for hand, prob in self.probabilities.items()])

        df = pd.merge(orig_df, prob_df, on=['players', 'hand'], how='outer')
        df.fillna(0, inplace=True)
        df['won'] = (df['won'] + df['new_won']).astype(int)
        df['played'] = (df['played'] + df['new_played']).astype(int)
        df['prob'] = df['won'] / df['played']
        new_hands_played = int(df['new_played'].sum())
        total_hands_played = df[df.players == self.num_players]['played'].sum()

        df = df[orig_df.columns].sort_values(['players', 'prob'], ascending=[True, False])
        df.to_csv(path, index=False)

        print(f"Players = {self.num_players}, New hands = {new_hands_played:,}, Total hands = {total_hands_played:,}.")


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
        self.hole_cards = None
        self.hand = None

    def __repr__(self):
        return f"Player({self.hole_cards})"

    def get_hand(self, community_cards):
        assert self.hole_cards is not None, 'Hole cards have not been dealt!'
        all_cards = self.hole_cards.cards + community_cards
        self.hole_cards = HoleCards(self.hole_cards.cards)
        self.hand = Hand(all_cards, self.hole_cards)
        return self.hand


class Card:
    rank_map = {**dict({'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}), **dict(zip(range(2, 11), range(2, 11)))}

    def __init__(self, rank, suit):
        assert rank in Deck.ranks
        assert suit in Deck.suits
        self.rank = rank
        self.rank_number = Card.rank_map[rank]
        self.suit = suit

    def __repr__(self):
        return f"{self.rank}{self.suit}"

    def __eq__(self, other):
        return self.rank_number == other.rank_number and self.suit == other.suit

    def __lt__(self, other):
        return self.rank_number < other.rank_number


class HoleCards:
    def __init__(self, cards: List[Card]):
        assert len(cards) == 2
        self.cards = cards
        self.cards.sort(reverse=True)
        self.suited = cards[0].suit == cards[1].suit

    def __repr__(self):
        return f"{self.cards[0].rank}{self.cards[1].rank}{'s' if self.suited else 'o'}"


class Deck:
    ranks = list(range(2, 10)) + ['A', 'K', 'Q', 'J', 'T']
    suits = ['s', 'c', 'h', 'd']

    def __init__(self):
        self.community_cards = []
        self.index = 0
        self.cards = [Card(rank, suit) for rank, suit in itertools.product(Deck.ranks, Deck.suits)]
        self.shuffle()

    def deal_hole_cards(self, players):
        for player in players:
            cards = self.deal_cards(2)
            player.hole_cards = HoleCards(cards)

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
        assert len(cards) == 7
        self.cards = list(cards)
        self.cards.sort(reverse=True)
        self.hole_cards = hole_cards if hole_cards is not None else []

        self.straight_cards = self.get_straight_cards(self.cards)
        self.straight_card_ranks = sorted(set([card.rank_number for card in self.straight_cards]), reverse=True)
        self.flush_cards = self.get_flush_cards(self.cards)
        self.straight_flush_cards = [card for card in self.straight_cards if card in self.flush_cards]
        self.rank_counts = self.get_rank_counts(self.cards)  # map of cunts to list of ranks

        self.score = self.get_score()

    def __repr__(self):
        return f"Hand({self.cards})"

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
        if len(self.straight_flush_cards) >= 5 and self.straight_flush_cards[0].rank == 'A':
            return 10
        else:
            return 0

    def score_straight_flush(self):
        if len(self.straight_flush_cards) >= 5:
            return 9 + self.straight_flush_cards[0].rank_number / 100
        else:
            return 0

    def score_four_of_a_kind(self):
        if 4 in self.rank_counts:
            four_card_rank = self.rank_counts[4][0]
            other_card_rank = max(card.rank_number for card in self.cards if card.rank_number != four_card_rank)
            return 8 + four_card_rank / 1e2 + other_card_rank / 1e4
        else:
            return 0

    def score_full_house(self):
        # check if we have 2 three of a kinds or 1 three of a kind and a pair
        three_card_ranks = self.rank_counts[3]
        pair_ranks = self.rank_counts[2]

        if len(three_card_ranks) == 2 or (len(three_card_ranks) == 1 and len(pair_ranks) > 0):
            other_three_card_rank = three_card_ranks[1] if len(three_card_ranks) == 2 else 0
            pair_card_rank = pair_ranks[0] if len(pair_ranks) > 0 else 0
            other_card_rank = max(other_three_card_rank, pair_card_rank)
            assert other_card_rank > 0
            return 7 + three_card_ranks[0] / 1e2 + other_card_rank / 1e4
        else:
            return 0

    def score_flush(self):
        return 6 + Hand.get_cards_score(self.flush_cards[:5]) if len(self.flush_cards) >= 5 else 0

    def score_straight(self):
        return 5 + self.straight_cards[0].rank_number / 1e2 if len(self.straight_cards) >= 5 else 0

    def score_three_of_a_kind(self):
        three_cards = self.rank_counts[3]

        if len(three_cards) > 0:
            high_cards = self.rank_counts[1]
            assert len(high_cards) >= 2
            return 4 + three_cards[0] / 1e2 + high_cards[0] / 1e4 + high_cards[1] / 1e6
        else:
            return 0

    def score_two_pair(self):
        pair_cards = self.rank_counts[2]

        if len(pair_cards) >= 2:
            high_cards = [card.rank_number for card in self.cards if card.rank_number not in pair_cards]
            return 3 + pair_cards[0] / 1e2 + pair_cards[1] / 1e4 + high_cards[0] / 1e6
        else:
            return 0

    def score_one_pair(self):
        pair_cards = self.rank_counts[2]

        if len(pair_cards) == 1:
            high_cards = [card for card in self.cards if card.rank_number != pair_cards[0]]
            return 2 + pair_cards[0] / 1e2 + Hand.get_cards_score(high_cards[:3]) / 1e2
        else:
            return 0

    def score_high_card(self):
        assert len(self.rank_counts[1]) >= 5
        return 1 + Hand.get_cards_score(self.cards[:5])

    @staticmethod
    def get_straight_cards(cards):
        # needs to take into account Ace high and low and pairs/trips etc.
        max_len = 1
        best_start_idx = 0
        best_end_idx = 0
        cur_start_idx = 0
        cards = cards + [card for card in cards if card.rank == 'A']  # add copy of Aces to the end

        for i, card in enumerate(cards):
            if (
                    (i == len(cards) - 1) or  # last card special case
                    (cards[i].rank_number - cards[i + 1].rank_number > 1) and  # consecutive or same
                    ~(cards[i].rank_number == 2 and cards[i + i].rank == 'A')  # low Ace special case
            ):
                seq_len = i - cur_start_idx + 1
                if seq_len > max_len:
                    max_len = seq_len
                    best_start_idx = cur_start_idx
                    best_end_idx = i
                cur_start_idx = i + 1

        return cards[best_start_idx:best_end_idx + 1]

    @staticmethod
    def get_flush_cards(cards):
        # get cards of the suit with the highest frequency
        suit_dict = {}
        max_suit = None
        max_suit_len = 0

        for card in cards:
            suit_cards = suit_dict.get(card.suit, []) + [card]
            suit_dict[card.suit] = suit_cards
            if len(suit_cards) > max_suit_len:
                max_suit = card.suit
                max_suit_len = len(suit_cards)

        return suit_dict[max_suit]

    @staticmethod
    def get_rank_counts(cards):
        rank_counts = collections.Counter([card.rank_number for card in cards])
        count_ranks = collections.defaultdict(list)

        for rank_number, count in sorted(rank_counts.items(), reverse=True):
            count_ranks[count].append(rank_number)
        return count_ranks

    @staticmethod
    def get_cards_score(cards):
        cards = cards if isinstance(cards, list) else [cards]
        score = 0
        for i, card in enumerate(cards):
            score += card.rank_number / (100 ** (i + 1))
        return score


if __name__ == '__main__':
    players = range(2, 6)
    num_processes = len(players)
    num_games = 13 * 13 * 10000

    start_time = time.time()

    # run sims
    result_queue = mp.Queue()
    processes = [mp.Process(target=Game(3).run_simulations, args=(num_games, result_queue))
                 for num_players in players]
    for p in processes:
        p.start()
    for p in processes:
        p.join()

    # store result
    result = [result_queue.get() for _ in processes]
    for game in result:
        game.store_probabilities()

    # print stats
    time_elapsed = time.time() - start_time
    print(f"Took {time_elapsed:.1f}s for {num_games} simulations. {num_games / time_elapsed:.0f} games/s => "
          f"{num_games / time_elapsed / 169:.1f} hands/s.")
