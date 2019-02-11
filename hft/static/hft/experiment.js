import { PolymerElement, html } from './node_modules/@polymer/polymer/polymer-element.js';

import {ELO} from './market_environments.js'


class ELOExperiment extends PolymerElement {

    static get properties(){
      return {
        environment: {type: Object, value: ELO},
        playerStatus: {type: Object},
        constants: {type: Object, value: OTREE_CONSTANTS}
      }
    }

    constructor(){
      super();
    }

    static get template() {
      return html`
        <market-session events={{environment.events}} 
        event-listeners={{environment.eventListeners}}
        event-handlers={{environment.eventHandlers}}
        </market-session>
        `;
      }
    }

customElements.define('elo-experiment', ELOExperiment);