import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';
import '../market-primitives/widgets/info-card.js'
import {} from '../node_modules/@polymer/polymer/lib/elements/dom-if.js';
class WallletCard extends PolymerElement {

    static get properties(){
      return {
        title: String,
        contentBottom: String,
        shineClass: String,
        inventory: Number,
        cash: Number,
        endowment: Number,
        signedVolume: Number,
        svSliderDisplayed: Boolean,
      };
    }
  
    constructor(){
      super();
    }
  
    static get template() {
      return html`  
        <style>
          :host {
            font-family: monospace;
          }
          .container {
            height: 100%;
            display: flex;
            align-items: center;
          }

          info-card{
            margin-top:5px;
          }

          .column{
            width: 100%;
            display: flex;
            flex-direction: column;
          }
          

        </style>

        <div class="container"> 
          <div class='column'>
            <info-card class="theCard" title="Gross Payoff" currency="ECU" value={{endowment}}>
            </info-card>
            <info-card class="theCard" title="Inventory" currency="" value={{inventory}}
              animated>
            </info-card>
            <info-card class="theCard" title="Cash" currency="ECU" value={{cash}}>
            </info-card>
            <template is="dom-if" if="{{svSliderDisplayed}}">
              <info-card class="theCard" title="Signed Volume" currency="" value={{signedVolume}}>
              </info-card>
            </template>
          </div>
        </div>
        `;
    }
  }  
  
customElements.define('elo-subject-wallet', WallletCard);
