import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';
import '../market-primitives/widgets/bounded-market-price-card.js'
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
          font-family: monospace;
          height: 100%;
          width: 100%;
        }
  
        .container {
          display: flex;
          justify-content:space-evenly;
          height:100%;
        }

        .bid-ask-container {
          margin:5px;
          display: flex;
          flex-direction: column;
          justify-content:center;
        }
        #bbo{
          display: flex;
          flex-direction: row;
          justify-content:center;
        }
        #mbbo{
          display: flex;
          flex-direction: row;
          justify-content:center;
        }

        #small-row {
          width: 35%;
          height: 100%;
          align-items: center;
        }
  
        </style>
          <div class="container">
            <div class="bid-ask-container">
              <div id="bbo">
                <bounded-market-price-card id="bid"  title="Best Bid" price={{bestBid}}
                  animated> 
                </bounded-market-price-card>
                <bounded-market-price-card id="ask" title="Best Ask" price={{bestOffer}}
                  animated> 
                </bounded-market-price-card>
              </div>
              <div id="mbbo">
                <bounded-market-price-card id="bid"  title="My Bid" price={{myBid}}> 
                </bounded-market-price-card>
                <br>
                <bounded-market-price-card id="ask" title="My Ask" price={{myOffer}}> 
                </bounded-market-price-card>
              </div>
            </div>
            <div id="small-row">
              <elo-subject-wallet inventory={{inventory}} cash={{cash}}
                endowment={{endowment}} signed-volume={{signedVolume}}> 
              </elo-subject-wallet>
            </div>
          </div>
        `;}
  
  }
  customElements.define('elo-info-table', InfoTable)