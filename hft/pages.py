from ._builtin import Page, WaitPage
import logging
from django.core.cache import cache
from django.conf import settings
import json
import time
from .output import InSessionTraderRecord
from .session_results import elo_player_summary, state_for_results_template
from .utility import ensure_results_ready

log = logging.getLogger(__name__)

# this module is under construction
# we will update this once we finish
# building the new environment components
 

class PreWaitPage(WaitPage):
    def after_all_players_arrive(self):
        pass

class EloExperiment(Page):
    pass

class ResultsWaitPage(WaitPage):

    def after_all_players_arrive(self):
        # at some point we should add a
        # wait page to otree that checks
        # for results being ready without
        # blocking a worker.
        # this should do it for now.
        players_query = self.group.get_players()
        subsession_id = self.subsession.id
        market_id = self.group.id
        if ensure_results_ready(
            subsession_id, market_id, InSessionTraderRecord, len(players_query)):
            for p in players_query:
                    most_recent_state_record = InSessionTraderRecord(
                        subsession_id=subsession_id, 
                        market_id=market_id, 
                        player_id=p.id,
                        trigger_event_type='market_end')
                    p.update_from_state_record(most_recent_state_record)
            try:
                for p in players_query:
                    elo_player_summary(p)
            except Exception:
                log.exception('error transform results group {}'.format(market_id))
        else:
            log.error('timeout transform results group {}'.format(market_id))

class Results(Page):
    def vars_for_template(self):
        page_state = state_for_results_template(self.player)
        # send as json so polymer likes it
        out = {k: json.dumps(v) for k, v in page_state.items()}
        return out

page_sequence = [
    PreWaitPage,
    EloExperiment,
    ResultsWaitPage,
    Results,
]