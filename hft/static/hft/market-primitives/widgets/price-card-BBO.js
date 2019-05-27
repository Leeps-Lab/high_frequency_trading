import { PolymerElement, html } from '../../node_modules/@polymer/polymer/polymer-element.js';

const MIN_BID = 0;
const MAX_ASK = 2147483647;

class PriceCardBBO extends PolymerElement {
     /*
    
        Market Best Bid and Offer Cards
        Bigger sizing than playerBBO cards

    */
  static get properties(){
  return {
    title: String,
    price: {type: String, value:0 ,observer: '_priceChanged'},
    price_trend: String,
    currency: String
    }
  }

  constructor(){
    super();
    //Set currency within the markup where it is initialized
    this.currency = '$';
  }

  _displayPrice(price) {
    let displayPrice = (price == MIN_BID || price == MAX_ASK) ? ' - ' : price
    return displayPrice
  }

  _priceChanged(newValue, oldValue) {
    let theCard = this.shadowRoot.querySelector('.cardPrice')
    if (newValue == MIN_BID || newValue == MAX_ASK) { 
      theCard.setAttribute("trend", "")
      return
    } 
    let incomingPriceTrend = oldValue > newValue ? 'price-down' : oldValue === newValue ? 
        '' : 'price-up';
    if (this.price_trend === incomingPriceTrend) {
      incomingPriceTrend = incomingPriceTrend + '-copy';
    }

    this.price_trend = incomingPriceTrend
    theCard.setAttribute("trend", incomingPriceTrend)
  }

  static get template() { 
    return html`
      <style>

      :host{
        display: inline-block;
        font-family: monospace;
        width:100px;
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
        font-size: 1.4em;
      }

      .title-text {
        text-align: center;
        font-size: 1.4em;
      }

      [trend=price-up]{
        animation-name: increase;
        animation-duration: 1s;
        animation-timing-function: ease-in-out;
      }

      [trend=price-up-copy]{
        animation-name: increase-more;
        animation-duration: 1s;
        animation-timing-function: ease-in-out;
      }

      [trend=price-down] {
        animation-name: decrease;
        animation-duration: 1s;
        animation-timing-function: ease-out;
      }

      [trend=price-down-copy] {
        animation-name: decrease-more;
        animation-duration: 1s;
        animation-timing-function: ease-out;
      }

      @keyframes increase{
        100% {
        background-color: rgba(0,255,0,0.4)
        };
        10% {
        background-color: rgba(0,255,0,0.05)
        };
      }

      @keyframes increase-more{
        100% {
        background-color: rgba(0,254,0,0.4)
        };
        10% {
        background-color: rgba(0,254,0,0.05)
        };
      }
      
      @keyframes decrease{
        100% {
        background-color: rgba(255,0,0,0.4)
        };
      }

      @keyframes decrease-more{
        100% {
        background-color: rgba(255,0,0,0.4)
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
              <div class="cardPrice">
                <p>
                  {{currency}}
                </p>
                <p id="the-price">
                  {{_displayPrice(price)}}
                </p>
              </div>
            </div>
        </div>    
        `;
      }
 }

customElements.define('price-card-bbo', PriceCardBBO)