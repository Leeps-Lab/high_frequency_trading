import { PolymerElement, html } from './node_modules/@polymer/polymer/polymer-element.js';

const MIN_BID = 0;
const MAX_ASK = 2147483647;

class MarketPriceCard extends PolymerElement {

  static get properties(){
  return {
    title: String,
    price: {type: String, observer: '_priceChanged'},
    price_trend: String,
    currency: String
    }
  }

  constructor(){
    super();
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
      }

      .fullCard {
        height: 100%;
        width: 100%;
        background: #FFFFF0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border: 1px solid #ccc;
        border-radius: 5px;
        box-shadow: 10 0px 0px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23);
      }

      .cardTitle {
        text-align: center;
        margin: 10px;
        font-weight: bold;
      }

      .cardPrice {
        display: flex;
        flex-direction: row;
        justify-content: center;
        border-top: 1px solid #000;
      }

      .title-text {
        display: inline-block;
        text-align: center;
        background-color: rgba(45, 45, 45, 0.1);
        font-size: 15px;
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
                <h1>
                  {{currency}}
                </h1>
                <h1 id="the-price">
                  {{_displayPrice(price)}}
                </h1>
              </div>
            </div>
        </div>    
        `;
      }
 }

customElements.define('market-price-card', MarketPriceCard)