from ._builtin import Page, WaitPage
import logging
from django.core.cache import cache
from django.conf import settings
import json
import time
from .output import HFTPlayerStateRecord, elo_player_summary, state_for_results_template

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
        results_ready = False
        timeout = 30
        sleep_time = 1
        total_slept = 0
        while total_slept < timeout:
            num_results_ready = HFTPlayerStateRecord.objects.filter(subsession_id=
                self.subsession.id, market_id=self.group.id, trigger_event_type=
                'market_end').count()
            num_players = self.group.player_set.count()
            log.warning('waiting for results for market {}, {}/{} results ready'.format(
                self.group.id, num_results_ready, num_players))            
            if  num_results_ready == num_players:
                results_ready = True
                break
            else:
                time.sleep(sleep_time)
                total_slept += sleep_time
        if results_ready:
            time.sleep(sleep_time)
            try:
                for p in self.group.get_players():
                    elo_player_summary(p)
            except Exception:
                log.exception('error transform results group {}'.format(self.group.id))
        else:
            log.error('timeout transform results group {}'.format(self.group.id))

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