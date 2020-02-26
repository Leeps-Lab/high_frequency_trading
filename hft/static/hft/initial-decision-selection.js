import { PolymerElement, html } from './node_modules/@polymer/polymer/polymer-element.js';

import {ELO} from './market-environments.js'
import './examples/elo-state-selection.js'

class InitialDecisionSelection extends PolymerElement {

    static get properties(){
      return {
        manualButtonDisplayed: {
          type: Boolean,
          value: OTREE_CONSTANTS.manualButtonDisplayed,
        },
        svSliderDisplayed: {
          type: Boolean,
          value: OTREE_CONSTANTS.svSliderDisplayed,
        },
        sliderDefaults: {
          type: Object,
          value: ELO.sliderProperties,
        },
        role: {
          type: String,
          value: 'out',
          reflectToAttribute: true,
        },
        speedOn: {
          type: Boolean,
          value: false,
          reflectToAttribute: true,
        },
        sliderAX: {
          type: Number,
          reflectToAttribute: true,
        },
        sliderAY: {
          type: Number,
          reflectToAttribute: true,
        },
        sliderAZ: {
          type: Number,
          reflectToAttribute: true,
        },
      }
    }

    static get template() {
      return html`
        <style>
            :host{
                /* Custom Color Variables */
                --my-bid-fill:#FAFF7F;
                --my-offer-fill:#41EAD4;
                /* Change in spread graph.js interpolateRGB */
                /* Unable to call var(style) within the d3 function */
                --other-bid-fill:#CC8400;
                --other-offer-fill:#00719E;

                --bid-cue-fill:#DEB05C;
                --offer-cue-fill:#5CA4C1;

                --bid-line-stroke:#FCD997;
                --offer-line-stroke:#99E2FF;
                --background-color-white:#FFFFF0;
                --background-color-blue:#4F759B;

                /*Background Color for sliders and on the attirbute graph*/
                --inv-color:#7DB5EC;
                --sv-color:#90ED7D;
                --ef-color:#8980F5;

                --global-font:monospace;
            }
        </style>
        <elo-state-selection
          manual-button-displayed="[[manualButtonDisplayed]]"
          sv-slider-displayed="[[svSliderDisplayed]]"
          slider-defaults="[[sliderDefaults]]"
          role="[[role]]"
          on-user-input="_handleInput"
          speed-on="[[speedOn]]"
        ></elo-state-selection>
      `;
    }

    _handleInput(event) {
      const msg = event.detail;
      switch (msg.type) {
        case 'role_change':
          this.role = msg.state;
          this.speedOn = false;
          break;
        case 'speed_change':
          this.speedOn = msg.value;
          break;
        case 'slider':
          this.sliderAX = parseFloat(msg.a_x);
          this.sliderAY = parseFloat(msg.a_y);
          this.sliderAZ = parseFloat(msg.a_z);
          break;
      }
    }
}

customElements.define('initial-decision-selection', InitialDecisionSelection);