from game import Game

class CoupCommander(object):
    def __init__(self):
        self.coup_game = Game()
        self.admins = ['caliscrub', 'gahitsu', 'hitsu']

    def get_response(self, target, response_text):
        response = {}
        response[target] = 'COUP: %s' % response_text
        return response

    def is_admin(self, name):
        return name.lower() in self.admins

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
foreignaid - foreign aid for 2 coins
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
    
    def exec_command(self, username, publicspace, comtext):
        com_items = comtext.split()
        command = com_items[0].lower()
        params = com_items[1:]
        if command == 'help':
            result = self.help_text()
            return self.get_response(username, result)
        if command == 'join':
            result = self.coup_game.add_player(username)
            return self.get_response(publicspace, result)
        elif command == 'start':
            result = self.coup_game.new_round()
            if 'New round has started' in result:
                messages = self.coup_game.get_all_private_statuses()
                messages[publicspace] = result
            else:
                messages = self.get_response(publicspace, result)
            return messages
        elif command == 'quit':
            result = self.coup_game.quit_game()
            return self.get_response(publicspace, result)
        elif command == 'viewcards':
            result = self.coup_game.get_private_status(username)
            return self.get_response(username, result)
        elif command in self.coup_game.actions:
            victim = None
            if len(params) > 0:
                victim = params[0]
            result = self.coup_game.perform_initiative_action(command, username, victimname=victim)
            return self.get_response(publicspace, result)
        elif command == 'steal':
            victim = params[0]
            result = self.coup_game.steal(username, victim)
            return self.get_response(publicspace, result)
        elif command == 'clearplayers':
            result = self.coup_game.clear_players()
            return self.get_response(publicspace, result)
        elif command == 'listplayers':
            result = self.coup_game.list_players()
            return self.get_response(publicspace, result)
        elif command == 'reseat':
            result = self.coup_game.random_reseat()
            return self.get_response(publicspace, result)
        elif command == 'status':
            result = self.coup_game.get_public_status()
            return self.get_response(publicspace, result)
        elif command == 'reveal':
            cardtype = params[0]
            result = self.coup_game.reveal(username, cardtype)
            return self.get_response(publicspace, result)
        elif command == 'ambreturn':
            cardtype = params[0]
            result = self.coup_game.ambassador_return(username, cardtype)
            return self.get_response(publicspace, result)
        elif command == 'challenge':
            result = self.coup_game.challenge(username)
            return self.get_response(publicspace, result)
        elif command == 'block':
            if len(params) > 0:
                cardtype = params[0]
                result = self.coup_game.block(username, cardtype)
            else:
                result = self.coup_game.block(username)
            return self.get_response(publicspace, result)
        elif command == 'score':
            result = self.coup_game.get_score()
            return self.get_response(publicspace, result)
        elif self.is_admin(username):
            if command == 'admin-nextturn':
                result = self.coup_game.get_next_turnowner()
                return self.get_response(publicspace, result)
            elif command == 'admin-kill':
                victim = params[0]
                cardtype = params[1]
                result = self.coup_game.kill_influence(victim, cardtype)
                return self.get_response(publicspace, result)
            elif command == 'admin-addmoney':
                victim = params[0]
                amt = int(params[1])
                result = self.coup_game.admin_add_money(victim, amt)
                return self.get_response(publicspace, result)
            elif command == 'admin-shuffle':
                result = self.coup_game.admin_shuffle()
                return self.get_response(publicspace, result)
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
                return self.get_response(publicspace, result)
            elif command == 'admin-return':
                player = params[0]
                index = int(params[1])
                result = self.coup_game.admin_return_card(player, index)
                return self.get_response(publicspace, result)
            elif command == 'admin-forceturn':
                player = params[0]
                result = self.coup_game.admin_force_turn_change(player)
                return self.get_response(publicspace, result)
        return self.get_response(publicspace, 'Unknown command')

