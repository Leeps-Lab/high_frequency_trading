from ._builtin import Page, WaitPage
import logging
from django.core.cache import cache
from django.conf import settings
import json
import time
from .output import TraderRecord
from .session_results import elo_player_summary, state_for_results_template
from .utility import ensure_results_ready
from settings import test_inputs_dir

log = logging.getLogger(__name__)

# this module is under construction
# we will update this once we finish
# building the new environment components
 

class PreWaitPage(WaitPage):
    def after_all_players_arrive(self):
        pass

class EloExperiment(Page):

    def vars_for_template(self):
        if not self.session.config['test_input_file']:
            inputs_addr = None
        else:
            inputs_addr = test_inputs_dir.format(
                self.session.config['test_input_file'])
        return {
            'inputs_addr': inputs_addr}

# class PostSessionWaitPage(WaitPage):
#     # I need an extra wait page
#     # since I am blocking at
#     # after all players arrive
#     # at actual wait page
#     template_name = 'hft/PostSessionWaitPage.html'

#     def socket_url(self):
#         return '/wait_page_results/{},{},{}/'.format(
#             self._session_pk,
#             self._index_in_pages,
#             self._channels_group_id_in_subsession()
#         )
#     def after_all_players_arrive(self):
#         print('arrived')

class PostSession(Page):
    timeout_seconds = 45
    timer_text = 'Processing results..'

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
            subsession_id, market_id, TraderRecord, len(players_query)):
            for p in players_query:
                    most_recent_state_record = TraderRecord.objects.get(
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
    PostSession,
    ResultsWaitPage,
    Results,
]
