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

  ready() {
    super.ready();
    this.currency = 'ECU';
  }

  animate() {
    const flashTime = 500;
    d3.select(this.$.cardPrice)
      .transition()
        .duration(flashTime/2)
        .ease(d3.easeLinear)
        .style('background-color', 'rgba(255,210,10,0.4)')
      .transition()
        .duration(flashTime/2)
        .ease(d3.easeLinear)
        .style('background-color', 'var(--background-color-white)');

    d3.select(this.$.triangle)
      .transition()
        .duration(flashTime/2)
        .ease(d3.easeLinear)
        .style('opacity', '1')
      .transition()
        .duration(flashTime/2)
        .ease(d3.easeLinear)
        .style('opacity', '0');
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
      #cardPrice {
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
      #triangle {
        opacity: 0;
      }
      </style>

        <div class="fullCard">
            <div class="cardContent">
              <div class="cardTitle">
                <span class="title-text">
                  {{title}}
                </span>
              </div>
              <div id="cardPrice" animate={{animated}}>
                <p id="the-price">
                  {{_displayPrice(price)}}
                </p>
              </div>
              <div>
                <span id="triangle">&#9650;</span>
              </div>
            </div>
        </div>    
        `;
      }
 }

customElements.define('bounded-market-price-card', MarketPriceCard)