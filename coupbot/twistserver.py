import sys
import re
import random
import coup

from twisted.words.protocols import irc
from twisted.internet import protocol, reactor

class CoupCommandDispatcher():
    coup_game = coup.Game()
    admin = 'caliscrub'

    def get_response(self, target, response_text):
        response = {}
        response['target'] = target
        response['response'] = 'COUP: %s' % response_text
        return response

    def help_text(self):
        helptext = """
Welcome to CaliCoup!

General Commands:
join - join the game
start - start the game
quit - end the game immediately
viewcards - view your cards
clearplayers - clear everyone from the game (if it's not currently running)
listplayers - list players
reseat - shuffle order of players (if not currently running)
status - view everyone's public status!

Action Commands (MAYBE NOT IMPLEMENTED YET):
income - take 1 coin
foreign - foreign aid for 2 coins
coup - remove another player's influence for 7 coins
steal - take 2 coins from someone with your captain(?)
tax = tax 3 coins with your duke(?)
hit = assassinate for 3 coins with your assassin(?)
block = block hits with your contessa(?)
block c = block steals with your captain(?)
block a = block steals with your ambassador(?)
exchange = exchange 2 cards with your ambassador(?)
challenge = call someone's bullshit!
"""
        return helptext
    
    def exec_command(self, username, channel, comtext):
        com_items = comtext.split()
        command = com_items[0].lower()
        params = com_items[1:]
        if command == 'help':
            result = self.help_text()
            return self.get_response(username, result)
        if command == 'join':
            result = self.coup_game.add_player(username)
            return self.get_response(channel, result)
        elif command == 'start':
            result = self.coup_game.new_round()
            return self.get_response(channel, result)
        elif command == 'quit':
            result = self.coup_game.quit_game()
            return self.get_resonse(channel, result)
        elif command == 'viewcards':
            result = self.coup_game.get_private_status(username)
            return self.get_response(username, result)
        elif command == 'steal':
            victim = params[0]
            result = self.coup_game.steal(username, victim)
            return self.get_response(channel, result)
        elif command == 'tax':
            result = self.coup_game.tax(username)
            return self.get_response(channel, result)
        elif command == 'income':
            result = self.coup_game.income(username)
            return self.get_response(channel, result)
        elif command == 'foreign':
            result = self.coup_game.foreignaid(username)
            return self.get_response(channel, result)
        elif command == 'clearplayers':
            result = self.coup_game.clear_players()
            return self.get_response(channel, result)
        elif command == 'listplayers':
            result = self.coup_game.list_players()
            return self.get_response(channel, result)
        elif command == 'reseat':
            result = self.coup_game.random_reseat()
            return self.get_response(channel, result)
        elif command == 'status':
            result = self.coup_game.get_public_status()
            return self.get_response(channel, result)
        elif command == 'reveal':
            cardtype = params[0]
            result = self.coup_game.reveal(username, cardtype)
            return self.get_response(channel, result)
        elif username.lower() == self.admin:
            if command == 'admin-nextturn':
                result = self.coup_game.get_next_turnowner()
                return self.get_response(channel, result)
            elif command == 'admin-kill':
                victim = params[0]
                cardtype = params[1]
                result = self.coup_game.kill_influence(victim, cardtype)
                return self.get_response(channel, result)
            elif command == 'admin-addmoney':
                victim = params[0]
                amt = int(params[1])
                result = self.coup_game.admin_add_money(victim, amt)
                return self.get_response(channel, result)
            elif command == 'admin-shuffle':
                result = self.coup_game.admin_shuffle()
                return self.get_response(channel, result)
            elif command == 'admin-see-deck':
                result = self.coup_game.admin_see_deck()
                return self.get_response(username, result)
            elif command == 'admin-see-deck-stats':
                result = self.coup_game.admin_see_deck_stats()
                return self.get_response(username, result)
            elif command == 'admin-draw':
                player = params[0]
                numdraw = int(params[1])
                result = self.coup_game.admin_draw(player, numdraw)
                return self.get_response(channel, result)
            elif command == 'admin-return':
                player = params[0]
                index = int(params[1])
                result = self.coup_game.admin_return_card(player, index)
                return self.get_response(channel, result)
        return self.get_response(channel, 'Unknown command')

class MyBot(irc.IRCClient):
    whycount = 0
    coins_flipped = 0
    coup_commander = CoupCommandDispatcher()
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def _reset_counters(self):
        self.coins_flipped = 0
    
    def signedOn(self):
        self.join(self.factory.channel, self.factory.channel_key)
        print "Signed on as {}.".format(self.nickname)
        self._reset_counters()

    def joined(self, channel):
        print "Joined %s." % channel

    def flipcoin(self):
        return random.choice(['heads', 'tails'])

    def privmsg(self, user, channel, msg):
        """
        Whenever someone says "why" give a lazy programmer response
        """
        #quitcommandmatch =
        username = user.split('!')[0]
        if msg.startswith('!die'):
            if username.lower() == 'caliscrub':
                response = 'i guess %s wants me to go...' % username
                self.msg(self.factory.channel, response)
                self.msg(username, 'you\'re so mean...')
                self.quit('a bloo bloo...')
            else:
                response = 'hell no, we won\'t go'
                self.msg(self.factory.channel, response)
        elif msg.startswith('!coin'):
            response = 'Flipping a coin... the result is %s!' % self.flipcoin()
            self.msg(self.factory.channel, response)
            self.coins_flipped = self.coins_flipped + 1
        elif msg.startswith('!flipcount'):
            response = 'The coin has been flipped %s times' % self.coins_flipped
            self.msg(self.factory.channel, response)
        elif msg.lower().startswith('!coup'):
            couptext = msg.split(None, 1)
            if len(couptext) > 1 and couptext[0].lower() == '!coup':
                command = couptext[1]
                result = self.coup_commander.exec_command(username, self.factory.channel, command)
                self.msg(result['target'], result['response'])

class MyBotFactory(protocol.ClientFactory):
    protocol = MyBot

    def __init__(self, nickname, channel, channel_key=None):
        self.nickname = nickname
        self.channel = channel
        self.channel_key = channel_key

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), NOT reconnecting." % reason
        #connector.connect()
        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % reason

if __name__ == "__main__":
    try:
        nick = sys.argv[1]
        channel = sys.argv[2]
        chan_key = None
        if len(sys.argv) == 4:
            chan_key = sys.argv[3]
        reactor.connectTCP('irc.esper.net', 6667, MyBotFactory(
            nickname=nick, channel=channel, channel_key=chan_key))
        reactor.run()
    except IndexError:
        print "Please specify a nickname & channel name."
        print "Example:"
        print "    python {} nick channel [channel_password]"\
            .format(sys.argv[0])

