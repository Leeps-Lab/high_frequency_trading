import { PolymerElement, html } from '../../node_modules/@polymer/polymer/polymer-element.js';
import './bounded-market-price-card.js'

class BidAskSpread extends PolymerElement {

    static get properties(){
      return {
        //FIND WAYS TO LOAD THESE VAUES IN ALL COMPONENTS?
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
      //Seperate HTML and CSS files into .tpl and .css files?
      return html`
        <style>
  
          :host {
            height:100%;
            width:100%;
          }

        </style>
  
        <div class="row-container">
          <bounded-market-price-card-BBO id="bid"  title={{titleLeft}} price={{bid}}> 
          </bounded-market-price-card>
          <bounded-market-price-card-BBO id="ask" title={{titleRight}} price={{ask}}> 
          </bounded-market-price-card>
        </div>
        `;
    }
  }  
  
customElements.define('bid-ask-spread', BidAskSpread)