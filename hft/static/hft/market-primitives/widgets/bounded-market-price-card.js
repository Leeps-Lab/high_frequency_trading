import { PolymerElement, html } from '../../node_modules/@polymer/polymer/polymer-element.js';

const MIN_BID = 0;
const MAX_ASK = 2147483647;

class MarketPriceCard extends PolymerElement {

  static get properties(){
  return {
    title: String,
    price: {
      type: String,
      value:0,
    },
    currency: String,
    sideId: String,
    animated: {type: String, reflectToAtrribute: true}
    }
  }

  constructor(){
    super();
    //Set currency within the markup where it is initialized
    this.currency = 'ECU';
  }

  animate() {
    let priceHolder = this.shadowRoot.querySelector('.cardPrice')
    this.animated = this.animated == 'animate_one' ? 'animate_two' : 'animate_one' 
      // interestingly polymer data binding did not reflect to dom somehow
      priceHolder.setAttribute("animate", this.animated)
  }

  _displayPrice(price) {
    if (price == MIN_BID || price == MAX_ASK) {
      return ' - '
    }
    else {
      return price + ' ' + this.currency;
    }
  }

  static get template() { 
    return html`
      <style>

      :host{
        display: inline-block;
        font-family: monospace;
        width:100%;
        height:100%;
      }

      .fullCard {
        text-align:center;
        background:var(--background-color-white);
        display: flex;
        flex-direction: column;
        justify-content: center;
        border: 1px solid #ccc;
        border-radius: 5px;
        box-shadow: 10 0px 0px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23);
      }
      .cardContent{
        width:100%;
        height:100%;
      }
      .cardPrice {
        display: flex;
        flex-direction: row;
        justify-content: center;
        border-top: 1px solid #000;
        font-size: 1.6em;
      }

      .title-text {
        text-align: center;
        font-size: 1.6em;
      }

      [animate=animate_one]{
        animation-name: shine;
        animation-duration: 0.2s;
        animation-timing-function: ease-out;

      }

      [animate=animate_two]{
        animation-name: shine-more;
        animation-duration: 0.2s;
        animation-timing-function: ease-out;

      }

      @keyframes shine{
        100% {
        background-color: rgba(255,215,10,0.4)
        };
      }

      @keyframes shine-more{
        100% {
        background-color: rgba(255,210,10,0.4)
        };
      }
      </style>

        <div class="fullCard">
            <div class="cardContent">
              <div class="cardTitle">
                <span class="title-text">
                  {{title}}
                </span>
              </div>
              <div class="cardPrice" animate={{animated}}>
                <p id="the-price">
                  {{_displayPrice(price)}}
                </p>
              </div>
            </div>
        </div>    
        `;
      }
 }

customElements.define('bounded-market-price-card', MarketPriceCard)