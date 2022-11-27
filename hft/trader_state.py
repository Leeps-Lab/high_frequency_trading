from .equations import latent_bid_and_offer
from .utility import market_is_valid
import logging

log = logging.getLogger(__name__)


class TraderStateFactory:
    @staticmethod
    def get_trader_state(model_id: str):
        if model_id == 'manual':
            return ELOManualTrader()
        elif model_id == 'out':
            return ELOOutState()
        elif model_id == 'automated':
            return ELOAutomatedTraderState()
        elif model_id == 'investor':
            return ELOInvestorState()
        else:
            raise Exception('unknown role: %s' % model_id)


class TraderState(object):

    event_dispatch = {}
    trader_model_name = ''

    def handle_event(self, trader, event):
        event_type = event.event_type
        if event_type in self.event_dispatch:
            log.debug('trader %s: handle %s event: %s' % (trader.tag, 
                event.event_type, event.message))
            handler_name = self.event_dispatch[event_type]
            handler = getattr(self, handler_name)
            handler(trader, event)
 
    def state_change(self, trader, event):
        pass
    
    def cancel_all_orders(self, trader, event):
        all_orders = trader.orderstore.all_orders()
        if all_orders:
            for order in all_orders:
                event.exchange_msgs('cancel', model=trader, **order)
                if order['buy_sell_indicator'] == 'B':
                    trader.staged_bid = None
                    log.debug('trader %s: staged bid set none.' % trader.tag)
                elif order['buy_sell_indicator'] == 'S':
                    trader.staged_offer = None
                    log.debug('trader %s: staged offer set none.' % trader.tag)

MIN_BID = 0
MAX_ASK = 2147483647


class ELOTraderState(TraderState):

    short_delay = 0.1
    long_delay = 0.5
    event_dispatch = { 
        'speed_change': 'speed_technology_change',
        'role_change': 'state_change', 
        'bbo_change': 'bbo_change', 
        'post_batch': 'post_batch', 
        'reference_price_change': 'reference_price_update',
        'signed_volume_change': 'signed_volume_change', 
        'external_feed_change': 'external_feed_change'}

    def state_change(self, trader, event):
        self.speed_technology_change(trader, event, value=False)
        self.cancel_all_orders(trader, event)
        if trader.disable_bid:
            trader.disable_bid = False
            log.debug('trader %s: bids enabled.' % trader.tag)
        if trader.disable_offer:
            trader.disable_offer = False        
            log.debug('trader %s: offers enabled.' % trader.tag)

    def speed_technology_change(self, trader, event, short_delay=short_delay, 
                                long_delay=long_delay, **kwargs):
        try:
            new_state = event.message.value
        except AttributeError:
            new_state = kwargs['value']
        trader.delayed = new_state
        if new_state is True:
            trader.delay = short_delay
            trader.technology_subscription.activate()
            log.debug('player %s subscribes to technology.' % trader.player_id)
        else:
            trader.delay = long_delay
            trader.technology_subscription.deactivate()
            speed_cost = trader.technology_subscription.invoice()
            trader.speed_cost += speed_cost
        event.broadcast_msgs('speed_confirm', value=new_state, model=trader)
    
    def bbo_change(self, trader, event):
        for field in ('best_bid', 'volume_at_best_bid', 'next_bid', 'best_offer',
            'volume_at_best_offer', 'next_offer'):
                trader.market_facts[field] = getattr(event.message, field)

    def post_batch(self, trader, event):
        for field in ('best_bid', 'volume_at_best_bid', 'next_bid', 'best_offer',
            'volume_at_best_offer', 'next_offer'):
                trader.market_facts[field] = getattr(event.message, field)

    def reference_price_update(self, trader, event):
        trader.market_facts['reference_price'] = event.message.reference_price

    def external_feed_change(self, trader, event):
        for field in ('e_best_bid','e_best_offer', 'e_signed_volume'):
            value = getattr(event.message, field)
            if value:
                trader.market_facts[field] = value
            
        
    def signed_volume_change(self, trader, event):
        signed_vol = event.message.signed_volume
        if trader.market_facts['signed_volume'] != signed_vol:
            trader.market_facts['signed_volume'] = signed_vol
        
    
class ELOOutState(ELOTraderState):
    trader_model_name = 'out'


class ELOManualTrader(ELOTraderState):
    trader_model_name = 'manual'
    event_dispatch = dict(**ELOTraderState.event_dispatch)
    event_dispatch.update(
        {'E': 'order_executed', 'order_entered': 'user_order'})

    def user_order(self, trader, event):
        buy_sell_indicator = event.message.buy_sell_indicator
        price = event.message.price
        if price == MIN_BID or price == MAX_ASK :
            return
        else:
            orders = trader.orderstore.all_orders(direction=buy_sell_indicator)
            if orders:
                for o in orders:
                    existing_token = o['order_token']
                    existing_buy_sell_indicator = o['buy_sell_indicator']
                    if buy_sell_indicator == existing_buy_sell_indicator:
                        order_info = trader.orderstore.register_replace(existing_token, price)
                        event.exchange_msgs('replace', model=trader, **order_info)
            else:
                order_info = trader.orderstore.enter(price=price,
                    buy_sell_indicator=buy_sell_indicator, time_in_force=99999)
                event.exchange_msgs('enter', model=trader, **order_info)
            if buy_sell_indicator == 'B':
                trader.staged_bid = price
            elif buy_sell_indicator == 'S':
                trader.staged_offer = price

    def order_executed(self, trader, event):
        order_info =  event.attachments['order_info']
        price = order_info['price']          
        buy_sell_indicator = order_info['buy_sell_indicator']      
        # do this check via order tokens if possible  
        if  buy_sell_indicator == 'B' and trader.staged_bid == price:
            trader.staged_bid = None   
        if  buy_sell_indicator == 'S' and trader.staged_offer == price:
            trader.staged_offer = None


class ELOAutomatedTraderState(ELOTraderState):
    trader_model_name = 'automated'
    event_dispatch = dict(**ELOTraderState.event_dispatch)
    event_dispatch.update({
            'E': 'order_executed',
            'slider': 'user_slider_change', 
        })

    def state_change(self, trader, event):
        super().state_change(trader, event)
        if trader.market_facts['best_bid'] > MIN_BID:
            log.debug('trader %s: market valid, enter buy..' % trader.tag)
            self.enter_order(trader, event, 'B')
        if trader.market_facts['best_offer'] < MAX_ASK:
            log.debug('trader %s: market valid, enter offer..' % trader.tag)
            self.enter_order(trader, event, 'S')
    
    def enter_order(self, trader, event, buy_sell_indicator, price=None,
            price_producer=latent_bid_and_offer, time_in_force=99999):
        log.debug('trader %s: enter order: %s' % (trader.tag, buy_sell_indicator))   
        if price is None: # then produce a price    
            mf = trader.market_facts
            if not market_is_valid(trader.market_facts):
                log.debug('trader %s:  enter order cancelled, market is invalid: %s' % (
                    trader.tag, trader.market_facts))     
                return
            trader.implied_bid, trader.implied_offer = price_producer(
                trader.best_bid_except_me,
                trader.best_offer_except_me,
                mf['signed_volume'],
                mf['e_best_bid'],
                mf['e_best_offer'],
                mf['e_signed_volume'],
                trader.inventory.position,
                a_x=trader.sliders['slider_a_x'],
                a_y=trader.sliders['slider_a_y'],
                a_z=trader.sliders['slider_a_z']
                )
            log.debug('trader %s: calculate price, set implied bid: %s, \
                        implied offer: %s' % ( trader.tag, trader.implied_bid, 
                            trader.implied_offer))   
            price = (trader.implied_bid if buy_sell_indicator == 'B' 
                                        else trader.implied_offer)      
        order_info = trader.orderstore.enter(
            price=price, buy_sell_indicator=buy_sell_indicator, 
            time_in_force=time_in_force)
        if buy_sell_indicator == 'B':
            trader.staged_bid = price
            log.debug('trader %s: set staged bid: %s' % (trader.tag, price))     
        elif buy_sell_indicator == 'S':
            trader.staged_offer = price    
            log.debug('trader %s: set staged offer: %s' % (trader.tag, price))    
        event.exchange_msgs('enter', model=trader, **order_info)
                       
    def bbo_change(self, trader, event):
        super().bbo_change(trader, event)
        if trader.disable_bid:
            trader.disable_bid = False
            log.debug('trader %s: bids enabled.' % trader.tag)
        if trader.disable_offer:
            trader.disable_offer = False        
            log.debug('trader %s: offers enabled.' % trader.tag)
        self.recalculate_market_position(trader, event)
    
    def external_feed_change(self, trader, event):
        super().external_feed_change(trader, event)
        self.recalculate_market_position(trader, event)
    
    def user_slider_change(self, trader, event):
        self.recalculate_market_position(trader, event)

    def validate_market_position(self, trader):
        bid, offer = None, None
        log.debug('trader %s: validating implied market position.' % trader.tag)
        if (trader.best_bid_except_me > MIN_BID) and (
            trader.implied_bid != trader.staged_bid):
            bid = trader.implied_bid
            log.debug('trader %s: implied bid valid.' % trader.tag)
        if (trader.best_offer_except_me < MAX_ASK) and (
            trader.implied_offer != trader.staged_offer):
            offer = trader.implied_offer
            log.debug('trader %s: implied offer valid.' % trader.tag)
        return bid, offer
    
    def recalculate_market_position(self, trader, event, 
                               price_producer=latent_bid_and_offer):
        log.debug('trader %s: recalculating market position...' % trader.tag)
        mf = trader.market_facts
        if not market_is_valid(trader.market_facts):
            log.debug('market not valid: %s' % trader.market_facts)
            return
        trader.implied_bid, trader.implied_offer = price_producer(
                trader.best_bid_except_me,
                trader.best_offer_except_me,
                mf['signed_volume'],
                mf['e_best_bid'],
                mf['e_best_offer'],
                mf['e_signed_volume'],
                trader.inventory.position,
                a_x=trader.sliders['slider_a_x'],
                a_y=trader.sliders['slider_a_y'],
                a_z=trader.sliders['slider_a_z'])
        log.debug('trader %s: calculate price, implied bid: %s, implied offer: %s' % ( 
                    trader.tag, trader.implied_bid, trader.implied_offer))   
        bid, offer = self.validate_market_position(trader)
        
        old_bid = trader.staged_bid 
        old_offer = trader.staged_offer
        start_from = 'B'
        if bid > old_offer:
            start_from = 'S'
        elif offer < old_bid:
            start_from = 'B'

        if bid or offer:
            self.adjust_market_position(
                trader, event, target_bid=bid, target_offer=offer, 
                start_from=start_from)

    def adjust_market_position(self, trader, event, target_bid=None, target_offer=None, 
            start_from='B'):
        sells = []
        log.debug('trader %s: adjust market position, suggested bid: %s, \
                suggested offer: %s' % (trader.tag, target_bid, target_offer))
        

        if target_offer is not None and trader.disable_offer is False:
            current_sell_orders = trader.orderstore.all_orders('S')
            if current_sell_orders:
                for order in current_sell_orders:
                    if ( target_offer != (order.get('replace_price', None)) or order['price'] ):
                        order_info = trader.orderstore.register_replace(
                            order['order_token'], target_offer)
                        sells.append(order_info)
                trader.staged_offer = target_offer
                log.debug('trader %s: adjust by replace, set staged offer: %s' % (
                            trader.tag, target_offer)) 
            else:
                self.enter_order(trader, event, 'S', price=target_offer)

        buys = []
        if target_bid is not None and trader.disable_bid is False:
            current_buy_orders = trader.orderstore.all_orders('B')
            if current_buy_orders:
                for order in current_buy_orders:
                    if ( target_bid != (order.get('replace_price', None) or order['price'] )  ):
                        order_info = trader.orderstore.register_replace(
                            order['order_token'], target_bid)
                        buys.append(order_info)
                trader.staged_bid = target_bid
                log.debug('trader %s: adjust by replace, set staged bid: %s' % (
                    trader.tag, target_bid))
            else:
                self.enter_order(trader, event, 'B', price=target_bid)

        if start_from == 'B':
            all_orders = buys + sells
        else:
            all_orders = sells + buys
        if all_orders:
            for order in all_orders:
                event.exchange_msgs('replace', model=trader, **order)

    def order_executed(self, trader, event):
        order_info = event.attachments['order_info']
        price = order_info['price']          
        buy_sell_indicator = order_info['buy_sell_indicator']

        if  buy_sell_indicator == 'B':
            trader.staged_bid = None      
            log.debug('trader %s: set staged bid to none from: %s ' % (
                    trader.tag, price)) 
        if  buy_sell_indicator == 'S':
            trader.staged_offer = None
            log.debug('trader %s: set staged offer to none from: %s ' % (
                    trader.tag, price)) 

        # given conditions below
        # bbo is stale
        mf = trader.market_facts
        # if buy_sell_indicator == 'B':
        #     if mf['volume_at_best_bid'] == 1 and mf['best_bid'] == price:
        #         trader.disable_bid = True
        # if buy_sell_indicator == 'S':
        #     if mf['volume_at_best_offer'] == 1 and mf['best_offer'] == price:
        #         trader.disable_offer = True


class ELOInvestorState(TraderState):
    trader_model_name = 'investor'
    event_dispatch = dict(**ELOTraderState.event_dispatch)
    event_dispatch.update({'investor_arrivals': 'enter_order'})

    def enter_order(self, trader, event):
        order_info = trader.orderstore.enter(**event.to_kwargs())
        event.exchange_msgs('enter', model=trader, **order_info)
