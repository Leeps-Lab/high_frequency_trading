# Goal: to first be able to read client's input and run it to Exchange
#       second to get output from exchange server and save it
#       third keep track of client's shares and cash

# Tasks:
#   1. Parsing functions for input
#   2. Set up wallet structure
#   3. Receive and parse output
#      Communication with another file for output (exchange.py line 116)
#      goes into wallet, communicate wallet with client, then client goes to exchange
#   4. Update wallet for buying and selling
#   5. Cash limitation for purchases
#   6. Add or withdraw cash

#   2&6 FM, 3&4 WMW, 1&5 JMC

import sys
import asyncio
import asyncio.streams
import configargparse
import logging as log
import re
import functools
# import binascii
from random import randrange
import itertools

from OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages

# Task 2: Set up wallet structure
class Trade_Station(object):
    def __init__(self, cash, id):
        self = self
        self.id = id
        self.cash = cash
        self.inventory = {}
        self.order_tokens = {}  # key = order token and value = 'B' or 'S'
        self.bid_stocks = {}  # stocks that you are bidding in market  key=order token and value = stock name
        self.ask_stocks = {}  # same as bid_stocks for key and value, this is needed cause executed messages dont return stock name
        self.bid_quantity = {}
        self.ask_quantity = {}

    def summary(self):  # should remove order_tokens when transaction is complete
        print("id:{} cash:{}\n"
              " inventory:{} \n"
              "order_token:{}\n"
              " bid_stocks{}\n"
              " ask_stocks{}\n"
              .format(self.id,
                      self.cash,
                      self.inventory,
                      self.order_tokens,
                      self.bid_stocks,
                      self.ask_stocks))

    def buy_share(self, share, price, amt):
        if(share not in self.inventory):
            self.inventory[share] = amt
        else:
            self.inventory[share] += amt
        self.cash -= amt*price

    def sell_share(self, share, price, amt):
        if(share not in self.inventory):
            #self.inventory[share] = amt
            print("You do not own these shares")
        else:
            self.inventory[share] -= amt
            self.cash += amt*price

    def get_id(self):
        return self.id
    def get_cash(self):
        return self.cash
    def get_inventory(self):
        return self.inventory

    # Task 6: Add and Withdraw Cash from Wallet
    def add_withdraw_cash(self):
        print("Do you want to add or withdraw cash? ")
        while(1):
            add_or_withdraw = input("Type A for add and W for withdraw. ")
            if (add_or_withdraw == 'A'):
                add = input("How much money do you want to add? ")
                self.cash += int(add)
                break;
            elif (add_or_withdraw == 'B'):
                sub = input("How much money do you want to withdraw? ")
                self.cash -= int(sub)
                break;
            else:
                print("Please try again.")





p = configargparse.ArgParser()
p.add('--port', default=9001)
p.add('--host', default='127.0.0.1', help="Address of server")
options, args = p.parse_known_args()


def main():
    user = Trade_Station(1000000, 1)

    log.basicConfig(level=log.DEBUG)
    log.debug(options)

    async def client():
        reader, writer = await asyncio.streams.open_connection(
            options.host,
            options.port,
            loop=loop)

        async def send(request):
            writer.write(bytes(request))
            await writer.drain()

        async def recv():
            try:
                header = (await reader.readexactly(1))
            except asyncio.IncompleteReadError:
                log.error('connection terminated without response')
                return None
            message_type = OuchServerMessages.lookup_by_header_bytes(header)
            try:
                payload = (await reader.readexactly(message_type.payload_size))
            except asyncio.IncompleteReadError as err:
                log.error('Connection terminated mid-packet!')
                return None

            response_msg = message_type.from_bytes(payload, header=False)
            return response_msg

        while True:
            message_type = OuchClientMessages.EnterOrder
            buy_sell = ""
            for index in itertools.count():
                b_or_sell = random.randint(0, 1)
                if b_or_sell == 0:
                    buy_sell = b'B'
                else:
                    buy_sell = b'S'

                str_buy_sell = buy_sell.decode('ascii')
                token = '{:014d}'.format(index).encode('ascii')
                token = token.decode('ascii')
                bstock = b'AMAZGOOG'
                stock = bstock.decode('ascii')
                price = 1000
                time_in_force = randrange(0, 99999)
                firm = b'OUCH'

                user.order_tokens[token] = str_buy_sell
                if (buy_sell == b'B'):
                    user.bid_stocks[token] = stock
                else:
                    user.ask_stocks[token] = stock

                request = message_type(
                    order_token='{:014d}'.format(index).encode('ascii'),
                    buy_sell_indicator = buy_sell,
                    shares=randrange(100, 5000),
                    stock=b'AMAZGOOG',
                    price=1000,
                    time_in_force=randrange(0, 99999),
                    firm=b'OUCH',
                    display=b'N',
                    capacity=b'O',
                    intermarket_sweep_eligibility=b'N',
                    minimum_quantity=1,
                    cross_type=b'N',
                    customer_type=b' ')
                log.info("Sending Ouch message: %s", request)
                await send(request)
                response = await recv()
                log.info("Received response Ouch message: %s:%d", response, len(response))

            # task 3 and 4, parses execute message and updates inventory and cash
                output = str(response)
                if output[0] == 'E':
                    parsed_token = output[18:32]
                    #cant just take preset list comprehension of this because prices and shares length is varied
                    cat = output[35:] #find the price and share from searching @
                    get_price = False
                    executed_shares = []
                    executed_price = []
                    print("output={}".format(output))
                    print("cat = {}".format(cat))
                    for i in cat:
                        if i == '@':
                            get_price = True
                        elif i == ':':
                            break
                        elif not get_price:
                            executed_shares.append(i)
                        else:
                            executed_price.append(i)

                    executed_shares = int(''.join(map(str,executed_shares)))
                    executed_price = int(''.join(map(str, executed_price)))
                    cost = executed_price * executed_shares
                    print("\nHere is the parsed token:{}\n".format(parsed_token))
                    print("\nHere are the executed_shares {}\n".format(executed_shares))
                    print("\nHere are the executed_price {}\n".format(executed_price))
                    if parsed_token in user.order_tokens and user.order_tokens[parsed_token] == 'B':

                        user.cash -= cost
                        share_name = [user.bid_stocks[i] for i in user.bid_stocks if i == parsed_token]
                        print("share_name={}".format(share_name))
                        user.inventory[share_name[0]] = executed_shares


                    elif parsed_token in user.order_tokens and user.order_tokens[parsed_token] == 'S':
                        user.cash += cost
                        share_name = [user.ask_stocks[i] for i in user.ask_stocks if i == parsed_token]
                        print("share_name={}".format(share_name))
                        user.inventory[share_name[0]] - executed_shares
                        if user.inventory[share_name[0]] == 0:
                            del user.inventory[share_name[0]]

                    user.summary()

                await asyncio.sleep(4.0)

        writer.close()
        asyncio.sleep(0.5)

    loop = asyncio.get_event_loop()
# creates a client and connects to our server
    try:
        loop.run_until_complete(client())
    finally:
        loop.close()


if __name__ == '__main__':
    main()
