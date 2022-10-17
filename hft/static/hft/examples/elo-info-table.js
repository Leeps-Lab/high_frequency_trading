import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';
import '../market-primitives/widgets/bounded-market-price-card.js'
import {} from '../node_modules/@polymer/polymer/lib/elements/dom-if.js';
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
        signedVolume: Number,
        svSliderDisplayed: Boolean,
        clearingPrice: {
          type: Object,
          value: {
            price: '-',
            volume: '-',
          }
        },
      }
    }
    
    ready() {
      super.ready();
      this.addEventListener('transaction', this._handleExecution);
     }

     _handleExecution(event) {
      if (event.detail.bid) {
        let theCard = this.$.my_bid
        theCard.animate()
      }
      if (event.detail.ask) {
        let theCard = this.$.my_ask
        theCard.animate()
      }
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
          display: flex;
          width:55%;
          height:100%;
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

        .clearing-info {
          text-align: center;
        }

        .clearing-info span {
          font-size: 1.4em;
          margin: 0.5em;
          display: block;
          background: var(--background-color-white);
        }

        </style>
          <div class="container">
            <div class="bid-ask-container">
              <div id="bbo">
                <bounded-market-price-card id="bid"  title="Best Bid" price={{bestBid}}> 
                </bounded-market-price-card>
                <bounded-market-price-card id="ask" title="Best Ask" price={{bestOffer}}>
                </bounded-market-price-card>
              </div>
              <div id="mbbo">
                <bounded-market-price-card id="my_bid" title="My Bid" price={{myBid}}> 
                </bounded-market-price-card>
                <br>
                <bounded-market-price-card id="my_ask" title="My Ask" price={{myOffer}}> 
                </bounded-market-price-card>
              </div>
              <div class="clearing-info" style$="{{_showClearingPrice()}}">
                <span>Clearing price: $\{{clearingPrice.price}} volume: {{clearingPrice.volume}}</span>
              </div>
            </div>
            <div id="small-row">

            <elo-subject-wallet inventory={{inventory}} cash={{cash}}
              endowment={{endowment}} signed-volume={{signedVolume}} sv-slider-displayed={{svSliderDisplayed}}> 
            </elo-subject-wallet>

            </div>
          </div>
        `;}

        _showClearingPrice() {
          return OTREE_CONSTANTS.auctionFormat == 'FBA' ? '' : 'display: none;'
        }
  
  }
  customElements.define('elo-info-table', InfoTable)