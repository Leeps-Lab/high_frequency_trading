# this is very specific for ELO experiment 
# so I will go right at it
# not abstracting for reuse
from otree.api import models
from otree.db.models import Model, ForeignKey
from .cache import get_cache_key
from django.core.cache import cache
from .output import TraderRecord
from .market_elements.subscription import Subscription
import logging

log = logging.getLogger(__name__)


class HFTPlayerSessionSummary(Model):
    subsession_id = models.StringField()
    player_id = models.IntegerField()
    market_id = models.IntegerField()
    signed_vol_sensitivity = models.FloatField(initial=0.0)
    inventory_sensitivity = models.FloatField(initial=0.0)
    external_feed_sensitivity = models.FloatField(initial=0.0)
    time_as_automated = models.FloatField(initial=0.0)
    time_as_out = models.FloatField(initial=0.0)
    time_as_manual = models.FloatField(initial=0.0)
    net_worth = models.IntegerField(initial=0)
    tax_paid = models.IntegerField(initial=0)
    speed_cost = models.IntegerField(initial=0)

    total_bids = models.IntegerField(initial=0)
    total_asks = models.IntegerField(initial=0)
    sum_bid_price = models.IntegerField(initial=0)
    sum_ask_price = models.IntegerField(initial=0)

    #subscriptionTime = models.IntegerField(initial=0)

def state_for_results_template(player):
    summary_objects = HFTPlayerSessionSummary.objects.filter(subsession_id=player.subsession.id, 
        market_id=player.market_id)
    nets = {str(o.player_id): o.net_worth * 0.0001 for o in summary_objects}
    taxes = {str(o.player_id): o.tax_paid * 0.0001 for o in summary_objects}
    print([o.speed_cost for o in summary_objects])
    speed_costs = {str(o.player_id): o.speed_cost * 0.0001 for o in summary_objects}
    names = {str(o.player_id): 'You' if o.player_id == player.id else 'Anonymous Trader' 
        for o in summary_objects}
    strategies = {str(o.player_id): {'automated': o.time_as_automated, 
        'manual': o.time_as_manual, 'out': o.time_as_out} for o in summary_objects}
    inv_sens = {str(o.player_id): o.inventory_sensitivity for o in summary_objects}
    signed_vol_sens = {str(o.player_id): o.signed_vol_sensitivity for o in summary_objects}
    ext_sensitivies = {str(o.player_id): o.external_feed_sensitivity for o in summary_objects}

    totalBids = {str(o.player_id): o.total_bids for o in summary_objects}
    totalAsks = {str(o.player_id): o.total_asks for o in summary_objects}
    sumBidPrice = {str(o.player_id): o.sum_bid_price for o in summary_objects}
    sumAskPrice = {str(o.player_id): o.sum_ask_price for o in summary_objects}

    '''
    mySummary = summary_objects.get(player_id=player.id)

    totalBids = mySummary.totalBids
    totalAsks = mySummary.totalAsks
    avgBidPrice = mySummary.avgBidPrice
    avgAskPrice = mySummary.avgAskPrice
    '''
    #subscriptionTime = mySummary.subscriptionTime

    return {'nets': nets, 'taxes': taxes, 'speed_costs': speed_costs, 'names': names, 'strategies': strategies, 
        'inv_sens': inv_sens, 'sig_sens': signed_vol_sens, 'ext_sens': ext_sensitivies, 'totalBids': totalBids, 
        'totalAsks': totalAsks, 'sumBidPrice': sumBidPrice, 'sumAskPrice': sumAskPrice}

def elo_player_summary(player):
    market = cache.get(get_cache_key('from_kws', model_name='market',
        model_id=player.market_id, subsession_id=player.subsession_id))
    session_length = market.time_session_end - market.time_session_start
    initial_sliders = {
        'slider_a_x': player.initial_slider_a_x,
        'slider_a_y': player.initial_slider_a_y,
        'slider_a_z': player.initial_slider_a_z,
    }
    average_sens = _get_average_sensitivies(player.subsession.id, player.market_id, player.id,
        market.time_session_start, market.time_session_end, initial_sliders)
    session_length_seconds = session_length.seconds
    percent_per_role = _calculate_role_time_percentage(market.role_group, player.id,
        session_length_seconds)

    cache_key = get_cache_key('from_kws',
                model_id=player.id,
                model_name='trader',
                subsession_id=player.subsession.id
            )
    trader = cache.get(cache_key)

    technology_subscription = Subscription(
            'speed_tech', player.id, .022)

    if(trader.total_bids != 0):
        avgBidPrice = trader.sum_bid_price / trader.total_bids
    else:
        avgBidPrice = 0
    
    if(trader.total_asks != 0):
        avgAskPrice = trader.sum_ask_price / trader.total_asks
    else:
        avgAskPrice = 0
    
    summary_object = HFTPlayerSessionSummary.objects.create(subsession_id=player.subsession.id, 
        market_id=player.market_id,
        player_id=player.id, 
        signed_vol_sensitivity=average_sens['slider_a_x'],
        inventory_sensitivity=average_sens['slider_a_y'], 
        external_feed_sensitivity=average_sens['slider_a_z'],
        time_as_automated=percent_per_role['automated'],
        time_as_out=percent_per_role['out'],
        time_as_manual=percent_per_role['manual'], 
        net_worth=player.net_worth,
        tax_paid=player.tax_paid,
        speed_cost=player.speed_cost,
        sum_bid_price=trader.sum_bid_price,
        sum_ask_price=trader.sum_ask_price,
        total_bids=trader.total_bids,
        total_asks=trader.total_asks
        #subscriptionTime=technology_subscription.subscriptionTimeTotal()
        )



def _get_average_sensitivies(subsession_id, market_id, player_id, session_start, session_end, initial_sliders):
    session_duration = (session_end - session_start).total_seconds()
    player_state_records = TraderRecord.objects.filter(subsession_id=subsession_id,
        market_id=market_id, player_id=player_id, trigger_event_type='slider').order_by('timestamp')
    slider_averages = {}
    for slider_name in ('slider_a_x', 'slider_a_y', 'slider_a_z'):
        slider_averages[slider_name] = 0
        current_slider_value = initial_sliders[slider_name]
        prev_change_time = session_start
        for record in player_state_records:
            slider_averages[slider_name] += current_slider_value * (record.timestamp - prev_change_time).total_seconds()
            current_slider_value = getattr(record, slider_name)
            prev_change_time = record.timestamp
        slider_averages[slider_name] += current_slider_value * (session_end - prev_change_time).total_seconds()
        slider_averages[slider_name] /= session_duration
        slider_averages[slider_name] = round(slider_averages[slider_name], 2)
    return slider_averages 

def _calculate_role_time_percentage(market_role_group, player_id, session_length):
    duration_per_role = {}
    for role_name in market_role_group.role_names:
        tracked_role = getattr(market_role_group, role_name)
        try:
            duration_per_role[role_name] = tracked_role.time_spent_per_player[player_id]
        except KeyError:
            duration_per_role[role_name] = 0
    total_time_in_session = sum(duration_per_role.values())
    if total_time_in_session == 0:
        log.exception(ValueError(
            'total time in session is 0 for player {}'.format(player_id)))
        duration_per_role['out'] = 1
        return duration_per_role
    normal_dur_per_role = {k: round(v / total_time_in_session, 2) for k, v in duration_per_role.items()}
    return normal_dur_per_role