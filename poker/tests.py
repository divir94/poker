import unittest
from simulation import *


class TestPokerHands(unittest.TestCase):
    high_card = Hand([Card(2, 's'), Card(3, 's'), Card(4, 's'), Card(5, 's'),
                      Card(7, 'c'), Card(9, 'c'), Card('J', 'c')])

    def test_straight_cards(self):
        # test simple
        cards = [Card(9, 's'), Card(8, 's'), Card(8, 'c'), Card(2, 's')]
        straight_cards = Hand.get_straight_cards(cards)
        self.assertEqual(straight_cards, cards[:3])

        # test pairs
        cards = [Card(9, 's'), Card(8, 's'), Card(8, 'c'), Card(7, 's')]
        straight_cards = Hand.get_straight_cards(cards)
        self.assertEqual(straight_cards, cards)

        # test no straight
        cards = [Card(9, 's'), Card(5, 's'), Card(2, 'c')]
        straight_cards = Hand.get_straight_cards(cards)
        self.assertEqual(straight_cards, [cards[0]])

        # test low ace
        cards = [Card('A', 'c'), Card(5, 's'), Card(2, 's')]
        straight_cards = Hand.get_straight_cards(cards)
        self.assertEqual(straight_cards, [cards[2], cards[0]])

    def test_flush_cards(self):
        # test simple
        cards = [Card(9, 'c'), Card(8, 's'), Card(5, 's'), Card(2, 's')]
        straight_cards = Hand.get_flush_cards(cards)
        self.assertEqual(straight_cards, cards[1:])

        # test pair
        cards = [Card(8, 'c'), Card(9, 's'), Card(8, 's'), Card(2, 's')]
        straight_cards = Hand.get_flush_cards(cards)
        self.assertEqual(straight_cards, cards[1:])

    def test_royal_flush(self):
        # test simple
        hand = Hand([Card(2, 's'), Card('A', 's'), Card('K', 's'), Card('Q', 's'), Card('J', 's'),
                     Card('T', 's'), Card(3, 'c')])
        self.assertEqual(hand.score_royal_flush(), 10)

        # test simple
        self.assertEqual(TestPokerHands.high_card.score_royal_flush(), 0)

        # test different suit
        hand = Hand([Card(2, 's'), Card('A', 'c'), Card('K', 's'), Card('Q', 's'), Card('J', 's'),
                     Card('T', 's'), Card(3, 'c')])
        self.assertEqual(hand.score_royal_flush(), 0)

    def test_straight_flush(self):
        # test simple
        hand = Hand([Card(2, 's'), Card('A', 's'), Card(3, 's'), Card(4, 's'), Card(5, 's'),
                     Card('A', 'c'), Card(3, 'c')])
        self.assertEqual(hand.score_straight_flush(), 9 + 5 / 1e2)
        self.assertEqual(TestPokerHands.high_card.score_straight_flush(), 0)

        # test different suit
        hand = Hand([Card(2, 's'), Card('A', 'c'), Card(3, 's'), Card(4, 's'), Card(5, 's'),
                     Card('T', 's'), Card(3, 'c')])
        self.assertEqual(hand.score_straight_flush(), 0)

    def test_four_of_a_kind(self):
        hand = Hand([Card(9, 's'), Card(9, 'c'), Card(9, 'd'), Card(9, 'h'),
                     Card('K', 's'), Card(7, 's'), Card(6, 's')])
        self.assertEqual(hand.score_four_of_a_kind(), 8 + 9 / 1e2 + 13 / 1e4)
        self.assertEqual(TestPokerHands.high_card.score_four_of_a_kind(), 0)

    def test_full_house(self):
        # test simple
        hand = Hand([Card('T', 's'), Card('T', 'c'), Card('T', 'd'), Card(2, 'h'), Card(2, 's'),
                     Card('A', 's'), Card(5, 's')])
        self.assertEqual(hand.score_full_house(), 7 + 10 / 1e2 + 2 / 1e4)
        self.assertEqual(TestPokerHands.high_card.score_full_house(), 0)

        # test 2 trips
        hand = Hand([Card('T', 's'), Card('T', 'c'), Card('T', 'd'), Card(2, 'h'), Card(2, 's'),
                     Card(2, 'c'), Card(5, 's')])
        self.assertEqual(hand.score_full_house(), 7 + 10 / 1e2 + 2 / 1e4)

        # test 2 pairs
        hand = Hand([Card('T', 's'), Card('T', 'c'), Card('T', 'd'), Card(2, 'h'), Card(2, 's'),
                     Card(5, 'c'), Card(5, 's')])
        self.assertEqual(hand.score_full_house(), 7 + 10 / 1e2 + 5 / 1e4)

    def test_flush(self):
        hand = Hand([Card('T', 's'), Card(9, 's'), Card(8, 's'), Card(5, 's'), Card(2, 's'),
                     Card(2, 's'), Card(2, 'h')])
        self.assertAlmostEqual(hand.score_flush(), 6 + 10 / 1e2 + 9 / 1e4 + 8 / 1e6 + 5 / 1e8 + 2 / 1e10, delta=1e-11)
        self.assertEqual(TestPokerHands.high_card.score_flush(), 0)

    def test_straight(self):
        # test simple
        hand = Hand([Card(7, 'c'), Card(6, 's'), Card(5, 's'), Card(4, 's'), Card(3, 's'),
                     Card('A', 'c'), Card('K', 'c')])
        self.assertEqual(hand.score_straight(), 5 + 7 / 1e2)
        self.assertEqual(TestPokerHands.high_card.score_straight(), 0)

        # test Ace low
        hand = Hand([Card(5, 'c'), Card(4, 's'), Card(3, 's'), Card(2, 's'), Card('A', 's'),
                     Card(7, 'c'), Card('T', 'c')])
        self.assertEqual(hand.score_straight(), 5 + 5 / 1e2)

        # test pair
        hand = Hand([Card(7, 'c'), Card(7, 's'), Card(6, 's'), Card(6, 'c'), Card(5, 's'),
                     Card(4, 'c'), Card(3, 'd')])
        self.assertEqual(hand.score_straight(), 5 + 7 / 1e2)

    def test_three_of_a_kind(self):
        hand = Hand([Card(9, 's'), Card(9, 'c'), Card(9, 'h'), Card(5, 's'), Card(4, 'd'),
                     Card(3, 's'), Card(2, 'd')])
        self.assertEqual(hand.score_three_of_a_kind(), 4 + 9 / 1e2 + 5 / 1e4 + 4 / 1e6)
        self.assertEqual(TestPokerHands.high_card.score_three_of_a_kind(), 0)

    def test_two_pair(self):
        # test simple
        hand = Hand([Card(9, 's'), Card(9, 'c'), Card(5, 'h'), Card(5, 's'), Card(4, 'd'),
                     Card(3, 's'), Card(2, 'd')])
        self.assertEqual(hand.score_two_pair(), 3 + 9 / 1e2 + 5 / 1e4 + 4 / 1e6)
        self.assertEqual(TestPokerHands.high_card.score_two_pair(), 0)

        # test 3 pairs
        hand = Hand([Card(9, 's'), Card(9, 'c'), Card(5, 'h'), Card(5, 's'), Card(3, 'd'),
                     Card(2, 's'), Card(2, 'd')])
        self.assertEqual(hand.score_two_pair(), 3 + 9 / 1e2 + 5 / 1e4 + 3 / 1e6)

    def test_one_pair(self):
        hand = Hand([Card('T', 'd'), Card(9, 's'), Card(9, 'c'), Card(5, 'h'), Card(4, 's'),
                     Card(3, 'd'), Card(2, 's')])
        self.assertAlmostEqual(hand.score_one_pair(), 2 + 9 / 1e2 + 10 / 1e4 + 5 / 1e6 + 4 / 1e8, delta=1e-11)
        self.assertEqual(TestPokerHands.high_card.score_one_pair(), 0)

    def test_high_card(self):
        hand = Hand([Card('T', 'd'), Card(9, 's'), Card(7, 'c'), Card(5, 'h'), Card(4, 's'),
                     Card(3, 's'), Card(2, 'd')])
        self.assertAlmostEqual(hand.score_high_card(), 1 + 10 / 1e2 + 9 / 1e4 + 7 / 1e6 + 5 / 1e8 + 4 / 1e10,
                               delta=1e-11)


if __name__ == '__main__':
    unittest.main()
