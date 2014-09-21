import unittest
from coup.player import Player
from coup.action import *

class CoupActionTest(unittest.TestCase):
    def setUp(self):
        self.player_one = Player('player_one')
        self.player_two = Player('player_two')

    def test_Income(self):
        self.player_one._money = 5
        testaction = Income(self.player_one)
        testaction.perform()
        self.assertEqual(6, self.player_one.get_money())

    def test_Steal(self):
        self.player_one._money = 3
        self.player_two._money = 8
        testaction = Steal(self.player_one)
        testaction.perform(self.player_two)
        self.assertEqual(5, self.player_one.get_money())
        self.assertEqual(6, self.player_two.get_money())

    def test_Steal_Poor(self):
        self.player_one._money = 3
        self.player_two._money = 1
        testaction = Steal(self.player_one)
        testaction.perform(self.player_two)
        self.assertEqual(4, self.player_one.get_money())
        self.assertEqual(0, self.player_two.get_money())

    def test_Steal_Zero(self):
        self.player_one._money = 3
        self.player_two._money = 0
        testaction = Steal(self.player_one)
        testaction.perform(self.player_two)
        self.assertEqual(3, self.player_one.get_money())
        self.assertEqual(0, self.player_two.get_money())

if __name__ == '__main__':
    unittest.main()
