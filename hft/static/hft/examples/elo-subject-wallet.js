import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';
import '../market-primitives/widgets/info-card.js'

class WallletCard extends PolymerElement {

    static get properties(){
      return {
        title: String,
        contentBottom: String,
        shineClass: String,
        inventory: Number,
        cash: Number,
        endowment: Number,
        signedVolume: Number
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
          .column{
            width: 100%;
            display: flex;
            flex-direction: column;
          }
          

        </style>

        <div class="container"> 
          <div class='column'>
            <info-card class="theCard" title="Cash" currency=$ value={{cash}}>
            </info-card>
            <info-card class="theCard" title="Inventory" currency="" value={{inventory}}>
            </info-card>
            <info-card class="theCard" title="Wealth" currency=$ value={{endowment}}>
            </info-card>
            <info-card class="theCard" title="Signed Volume" currency="" value={{signedVolume}}>
            </info-card>
          </div>
        </div>
        `;
    }
  }  
  
customElements.define('elo-subject-wallet', WallletCard);
