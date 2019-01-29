import { LitElement, html } from '../node_modules/lit-element/lit-element.js';

  
class MarketPriceCard extends LitElement {

  static get properties(){
  return {
    title: {type: String},
    price: {type: Number},
    price_trend: {type: String},
    currency: {type: String}
    }
  }

  constructor(){
    super();
    this.title = '';
    this.price = 0;
    this.currency = '$';
    this.price_trend = '';
  }

  render(){ 
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
        box-shadow: 0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23);
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

      [trend=price-up-backup]{
        animation-name: increase-more;
        animation-duration: 1s;
        animation-timing-function: ease-in-out;
      }

      [trend=price-down] {
        animation-name: decrease;
        animation-duration: 1s;
        animation-timing-function: ease-in-out;
      }

      [trend=price-down-backup] {
        animation-name: decrease-more;
        animation-duration: 1s;
        animation-timing-function: ease-in-out;
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
        10% {
          background-color: rgba(0,255,0,0.05)
          };
      }

      @keyframes decrease-more{
        100% {
        background-color: rgba(255,0,0,0.4)
        };
        10% {
          background-color: rgba(0,255,0,0.05)
          };
      }

      </style>

        <div class="fullCard">
            <div class="cardContent">
              <div class="cardTitle">
                <span class="title-text">
                  ${this.title}
                </span>
              </div>
              <div class="cardPrice" trend=${this.price_trend}>
                <h1>
                  ${this.currency}
                </h1>
                <h1 id="the-price">
                  ${this.price}
                </h1>
              </div>
            </div>
        </div>    
        `;
      }
 }

customElements.define('market-price', MarketPriceCard)