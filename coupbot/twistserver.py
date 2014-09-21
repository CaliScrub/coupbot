import sys
import re
import random
import coup

from twisted.words.protocols import irc
from twisted.internet import protocol, reactor

class MyBot(irc.IRCClient):
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)
    
    def __init__(self, *args, **kwargs):
        self.coins_flipped = 0
        self.coup_commander = coup.CoupCommander()
    
    def is_admin(self, name):
        return name.lower() in self.admins
    
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

    def send_messages(self, messagetable):
        """
        Sends messages from a table which defines recipients as keys and messages as values.
        """
        for recipient in messagetable.iterkeys():
            self.msg(recipient, messagetable[recipient])
    
    def privmsg(self, user, channel, msg):
        """
        Handles messages received
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
                self.send_messages(result)

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
        print "Args were %s" % str(sys.argv)
        print "Please specify a nickname & channel name."
        print "Example:"
        print "    python {} nick channel [channel_password]"\
            .format(sys.argv[0])

