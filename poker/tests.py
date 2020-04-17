import unittest
from poker.simulation import *


class TestPokerHands(unittest.TestCase):
    high_card = Hand([Card(2, 'Spades'), Card(3, 'Spades'), Card(4, 'Spades'), Card(5, 'Spades'), Card(7, 'Clubs')])

    def test_royal_flush(self):
        ranks = ['Ace', 'King', 'Queen', 'Jack', 10]
        flush_hand = Hand([Card(rank, 'Spades') for rank in ranks])
        self.assertEqual(flush_hand.score_royal_flush(), 10)
        self.assertEqual(TestPokerHands.high_card.score_royal_flush(), 0)

    def test_straight_flush(self):
        hand = Hand([Card(rank, 'Spades') for rank in range(2, 7)])
        self.assertEqual(hand.score_straight_flush(), 9 + 6 / 100)
        self.assertEqual(TestPokerHands.high_card.score_straight_flush(), 0)

    def test_four_of_a_kind(self):
        hand = Hand([Card(10, 'Spades'), Card(10, 'Clubs'), Card(10, 'Diamonds'), Card(10, 'Hearts'),
                     Card('King', 'Spades')])
        self.assertEqual(hand.score_four_of_a_kind(), 8 + 10 / 1e2 + 13 / 1e4)
        self.assertEqual(TestPokerHands.high_card.score_four_of_a_kind(), 0)

    def test_full_house(self):
        hand = Hand([Card(10, 'Spades'), Card(10, 'Clubs'), Card(10, 'Diamonds'), Card(2, 'Hearts'),
                     Card(2, 'Spades')])
        self.assertEqual(hand.score_full_house(), 7 + 10 / 1e2 + 2 / 1e4)
        self.assertEqual(TestPokerHands.high_card.score_full_house(), 0)

    def test_flush(self):
        hand = Hand([Card(10, 'Spades'), Card(9, 'Spades'), Card(8, 'Spades'), Card(5, 'Spades'),
                     Card(2, 'Spades')])
        self.assertAlmostEqual(hand.score_flush(), 6 + 10 / 1e2 + 9 / 1e4 + 8 / 1e6 + 5 / 1e8 + 2 / 1e10, delta=1e-11)
        self.assertEqual(TestPokerHands.high_card.score_flush(), 0)

    def test_straight(self):
        hand = Hand([Card(10, 'Spades'), Card(9, 'Hearts'), Card(8, 'Spades'), Card(7, 'Spades'),
                     Card(6, 'Spades')])
        self.assertEqual(hand.score_straight(), 5 + 10 / 1e2)
        self.assertEqual(TestPokerHands.high_card.score_straight(), 0)

    def test_three_of_a_kind(self):
        hand = Hand([Card(10, 'Spades'), Card(10, 'Clubs'), Card(10, 'Hearts'), Card(5, 'Spades'),
                     Card(2, 'Spades')])
        self.assertEqual(hand.score_three_of_a_kind(), 4 + 10 / 1e2 + 5 / 1e4 + 2 / 1e6)
        self.assertEqual(TestPokerHands.high_card.score_three_of_a_kind(), 0)

    def test_two_pair(self):
        hand = Hand([Card(10, 'Spades'), Card(10, 'Hearts'), Card(8, 'Spades'), Card(8, 'Hearts'),
                     Card(3, 'Spades')])
        self.assertEqual(hand.score_two_pair(), 3 + 10 / 1e2 + 8 / 1e4 + 3 / 1e6)
        self.assertEqual(TestPokerHands.high_card.score_two_pair(), 0)

    def test_one_pair(self):
        hand = Hand([Card(10, 'Spades'), Card(10, 'Hearts'), Card(8, 'Spades'), Card(5, 'Spades'),
                     Card(2, 'Spades')])
        self.assertAlmostEqual(hand.score_one_pair(), 2 + 10 / 1e2 + 8 / 1e4 + 5 / 1e6 + 2 / 1e8, delta=1e-11)
        self.assertEqual(TestPokerHands.high_card.score_one_pair(), 0)

    def test_high_card(self):
        hand = Hand([Card(10, 'Spades'), Card(9, 'Hearts'), Card(8, 'Spades'), Card(5, 'Spades'),
                     Card(2, 'Spades')])
        self.assertAlmostEqual(hand.score_high_card(), 1 + 10 / 1e2 + 9 / 1e4 + 8 / 1e6 + 5 / 1e8 + 2 / 1e10, delta=1e-11)


if __name__ == '__main__':
    unittest.main()
