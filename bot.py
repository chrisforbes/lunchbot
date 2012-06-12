#!/usr/bin/env python2

"""A really simple IRC bot."""

import sys
from twisted.internet import reactor, protocol
from twisted.words.protocols import irc

orders = {}
menus = {
    'lbq': [
        [ 'Quesadilla (needs 3 options)' , 'cheese and your choice of 3 fillings in a toasted tortilla with sour chream. Fillings are: smoky chicken, chorizo, salami, jalapenos, tomato, spinach, roasted red peppers, red onion, chipotle sauce, pesto, mozzarella, blue cheese cream cheese, brie, feta. $12' ],
        [ 'Vegetable curry' , 'Paneer, chickpea and vegetable curry with rice and beer naan. $15' ],
        [ 'Steak & stout pie' , 'Steak and cheddar pie with craft stout gravy and shoestring fries. $17' ],
        [ 'Chicken salad' , 'Harissa marinated chicken salad with roasted beetroot, rocket, grilled halloumi and walnuts in a citrus vinaigrette. $16' ],
        [ 'Fish & chips' , 'Emerson\'s Pilsner battered fish and chips with housemade sauces and salad greens. $19' ],
        [ 'Open chicken sandwich' , 'spicy marinated chicken breast with melted brie, salad greens, caramelised onions and garlic mayonnaise on sourdough served with shoestring fries and aioli. $18' ],
        [ 'Beef burger' , '220g beef patty, streaky bacon, onion rings, roasted beetroot and cheddar with beer-battered chunky fries and aiolo. $19' ],
        [ 'Margherita pizza' , 'fresh basil, cherry tomatoes, mozzarella and tomato sauce. $14' ],
        [ 'Beer garden pizza' , 'spinach, roasted pumpkin, pinenuts, rocket pesto and feta cheese. $16' ],
        [ 'Smokin\' chicken pizza' , 'smoked chicken breast, red onions, jalapenos with cream cheese and smoky chipotle BBQ sauce. $18' ],
        [ 'Spicy sausage pizza' , 'pepperoni, chorizo and mozzarella with sundried tomato pesto. $18' ],
        [ 'Four wheel drive pizza' , 'peppered steak, field mushrooms, rocket and blue cheese. $19' ],
        [ 'Pizza of the day' , 'our chef\'s culinary creation. p.o.a' ]
    ]
}

menu = None

protocols = []

def maybe_int(x):
    try: return int(x)
    except: return -1   # bs

class Bot(irc.IRCClient):
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def signedOn(self):
        self.join(self.factory.channel)
        self.channel = self.factory.channel
        protocols.append(self)
        print "Signed on as %s." % self.nickname

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        protocols.remove(self)

    def joined(self, channel):
        print "Joined %s." % channel

    def act(self, user, channel, cmd):
        username = user.split('!',1)[0]
        global orders, menu
        parts = cmd.split(' ',2)
        op = parts[0]
        if op == 'help':
            self.msg(channel, '!help: show this message.')
            self.msg(channel, '!menu: show the menu.')
            self.msg(channel, '!info <n>: show info for an item on the menu.')
            self.msg(channel, '!order [<nick>] <n> <special instructions>: order your lunch. `no beetroot` etc can go in `special instructions`')
            self.msg(channel, '!cancel: cancel your order')
            self.msg(channel, '!list: list current lunch orders')
            self.msg(channel, '!open <menu>: open orders for today, clear state')
            self.msg(channel, '!close: close orders')

        if op == 'order':
            if not menu:
                self.msg(channel, 'orders are not open.')
                return

            if len(parts) < 2:
                self.msg(channel, 'i\'m confused about what you wanted.')
                return

            item = maybe_int(parts[1])
            if item == -1 and len(parts) > 2:
                parts = cmd.split(' ',3)
                username = parts.pop(1)
                item = maybe_int(parts[1])
            if item < 0 or item >= len(menu):
                self.msg(channel, 'that\'s not a thing.')
                return

            special = len(parts) > 2 and parts[2] or None

            if not username in orders:
                orders[username] = []

            orders[username].append((item,special))
            if special:
                msgAll('%s added a %s, with instructions: %s.' % \
                    (username, menu[item][0], special))
            else:
                msgAll('%s added a %s.' % (username, menu[item][0]))

        if op == 'menu':
            if not menu:
                self.msg(channel, 'orders are not open.')
                return

            self.msg(channel, 'menu:')
            for i,m in enumerate(menu):
                self.msg(channel, '%d) %s' % (i,m[0]))
            self.msg(channel, '-- end of menu --');

        if op == 'info':
            if not menu:
                self.msg(channel, 'orders are not open.')
                return

            if len(parts) < 2:
                self.msg(channel, 'i\'m confused about what you wanted info on.')

            item = maybe_int(parts[1])
            if item < 0 or item >= len(menu):
                self.msg(channel, 'that\s not a thing.')
                return

            self.msg(channel, '%d) %s - %s' % (item, menu[item][0], menu[item][1]))

        if op == 'cancel':
            if not menu:
                self.msg(channel, 'orders are not open.')
                return

            if len(parts) > 1:
                parts = cmd.split(' ',2)
                username = parts.pop(1)
            if username not in orders:
                self.msg(channel, 'you don\'t have anything ordered!')
            else:
                del orders[username]
                msgAll('%s cancelled their order.' % username)

        if op == 'list':
            if not menu:
                self.msg(channel, 'orders are not open.')
                return

            self.msg(channel, '%d orders for today:' \
                % sum(len(v) for _,v in orders.items()))
            by_type = pivot_to_values(flatten_values(orders))
            for o,n in sorted(by_type.items(), key=lambda x:len(x[1])):
                instr = o[1] and '(%s) ' % (o[1],) or ''
                self.msg(channel, '%dx %s %s[%s]' % \
                    (len(n), menu[o[0]][0], instr, ','.join(n)))
            self.msg(channel, '-- end of orders --');

        if op == 'open':
            if len(parts) < 2:
                self.msg(channel, 'you didn\'t specify a menu. valid menus are:');
                for mn in menus.keys():
                    self.msg(channel, '* %s' % (mn,))
            if parts[1] not in menus:
                self.msg(channel, '%s is not a known menu.' % (parts[1],))
            menu = menus[parts[1]]
            orders = {}
            msgAll('orders are now open for %s!' % (parts[1],))

        if op == 'close':
            msgAll('orders are now closed.');
            orders = {}
            menu = None

    def privmsg(self, user, channel, msg):
        print 'channel: `%s` user: `%s` msg: `%s`' % (user, channel, msg)
        if msg.startswith('!'):
            self.act( user, channel, msg[1:] )
        elif msg.startswith('lunchbot: '):
            self.act( user, channel, msg[10:] )

def flatten_values(xs):
    for k,x in xs.items():
        for x_ in x: yield (k,x_)

def pivot_to_values(xs):
    result = {}
    for k,v in xs:
        if v not in result: result[v] = [k]
        else: result[v].append(k)
    return result

def msgAll(msg):
    for protocol in protocols:
        protocol.msg(protocol.channel, msg)

class BotFactory(protocol.ClientFactory):
    protocol = Bot

    def __init__(self, channel, nickname='lunchbot'):
        self.channel = channel
        self.nickname = nickname

    def clientConnectionLost(self, connector, reason):
        print "Connection lost. Reason: %s" % reason
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed. Reason: %s" % reason

if __name__ == "__main__":
    reactor.connectTCP('irc.wgtn.cat-it.co.nz', 6667, BotFactory('#lunch'))
    reactor.connectTCP('irc.freenode.org', 6667, BotFactory('#catalystlunch'))
    reactor.run()
