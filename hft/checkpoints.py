from .output import (HFTEventRecord, HFTPlayerStateRecord, HFTInvestorRecord,
    from_trader_to_player)
import logging

log = logging.getLogger(__name__)

def hft_trader_checkpoint(player_id, subject_state, event_dict):
    from .models import Player
    try:
        player = Player.objects.get(id=player_id)
        player = from_trader_to_player(player, subject_state)
        player_record = HFTPlayerStateRecord().from_event_and_player(event_dict, player)
        player_record.save()
    except Exception as e:
        log.exception('error post processing event: %s:%s' % (event_dict, e) )
    
def hft_event_checkpoint(event_dict):
    event_record = HFTEventRecord().from_event(event_dict)
    event_record.save()

def hft_investor_checkpoint(event):
    investor_record = HFTInvestorRecord().from_event(event)
    investor_record.save()