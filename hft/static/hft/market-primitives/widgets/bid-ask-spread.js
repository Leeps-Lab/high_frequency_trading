import { PolymerElement, html } from '../../node_modules/@polymer/polymer/polymer-element.js';
import './bounded-market-price-card.js'

class BidAskSpread extends PolymerElement {

    static get properties(){
      return {
        titleLeft: String,
        titleRight: String,
        bid: Number,
        ask: Number
      }
    }
  
    constructor(){
      super();
    }

    static get template() {
      return html`
        <style>
  
          :host {
            display: inline-block;
            width: 100%;
            height: 100%;
          }
  
          .row-container {
            display: flex;
            flex-direction: row;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: 100%;
          }

          .bo {
            width: 40%;
          }
        </style>
  
        <div class="row-container">
          <bounded-market-price-card id="bid" class="bo" title={{titleLeft}} price={{bid}}> 
          </bounded-market-price-card>
          <bounded-market-price-card id="ask" class="bo" title={{titleRight}} price={{ask}}> 
          </bounded-market-price-card>
        </div>
        `;
    }
  }  
  
customElements.define('bid-ask-spread', BidAskSpread)