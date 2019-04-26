import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';
import '../market-primitives/widgets/bid-ask-spread.js'
import './elo-subject-wallet.js'

class InfoTable extends PolymerElement {
    static get properties() {
      return {
        bestBid: Number,
        bestOffer: Number,
        myBid: Number,
        myOffer: Number,        
        inventory: Number, 
        cash: Number,
        endowment: Number,
        signedVolume: Number
      }
    }
    constructor() {
      super();
    }

    static get template() { 
        return html`
  
        <style>
        :host {
          display: inline-block;
          height: 100%;
          width: 100%;
          font-family: monospace;
        }
  
        .container {
          display: flex;
          flex-direction: row;
          justify-content: flex-start;
          align-items: center;
          height: 100%;
          width: 100%;
          background: #4F759B;
        }

        .title {
          display: inline-block;
          width: 33%;
          text-align: center;
          background: #FFFFF0;
        }
  
        .row {
          display: inline-block;
          margin: 5px;
          width: 33%;
          height: 100%;
        }

        #small-row {
          margin: 5px;
          width: 34%;
          height: 100%;
          align-items: flex-start;
        }
  
        </style>
          <div class="container">
            <div class="row">
              <bid-ask-spread title-left="Best Bid" title-right="Best Ask"
                bid={{bestBid}} ask={{bestOffer}}>
              </bid-ask-spread>
            </div>
            <div class="row">
              <bid-ask-spread title-left="My Bid" title-right="My Ask"
                bid={{myBid}} ask={{myOffer}}>
              </bid-ask-spread>
            </div>
            <div id="small-row" class="row">
              <elo-subject-wallet inventory={{inventory}} cash={{cash}}
                endowment={{endowment}} signed-volume={{signedVolume}}> 
              </elo-subject-wallet>
            </div>
          </div>
        `;}
  
  }
  customElements.define('elo-info-table', InfoTable)