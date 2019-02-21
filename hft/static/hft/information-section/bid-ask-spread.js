import { LitElement, html } from '../node_modules/lit-element/lit-element.js';


class BidAskSpread extends LitElement {

    static get properties(){
      return {
        titleLeft: {type: String},
        titleRight: {type: String},
        bid: {type: Number},
        ask: {type: Number},
        bidTrend: {type: String},
        askTrend: {type: String}
      }
    }
  
    constructor(){
      super();
      this.bid = 0;
      this.ask = 0;
      this.bidTrend = '';
      this.askTrend = '';
    }

    render() {
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
          <market-price id="bid" class="bo" title=${this.titleLeft} price=${this.bid}
            price_trend=${this.bidTrend}> </market-price>
          <market-price id="ask" class="bo" title=${this.titleRight} price=${this.ask}
            price_trend=${this.askTrend}> </market-price>
        </div>
        `;
    }
  }  
  
customElements.define('bidask-spread', BidAskSpread)