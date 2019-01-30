import { LitElement, html } from '../node_modules/lit-element/lit-element.js';

class InfoTable extends LitElement {

    static get properties() {
      return {
        title: {type: String},
        bbo: {type: Object},
        mbo: {type: Object},
        ice: {type: Object},
      }
    }

    constructor() {
      super();
      this.bbo = {'bid': 0, 'ask': 0, 'bid_trend': '', 'ask_trend': ''}
      this.mbo = {'bid': 0, 'ask': 0, 'bid_trend': '', 'ask_trend': ''}
      this.ice = {'inventory': 0, 'cash': 0, 'endowment': 0, 'shine_class': ''}
      
      this.addEventListener('click', this.updateState.bind(this));
    }
  
    updateState(fieldName, subFieldName, newValue) {
      // the single entry point for info table

      if (fieldName == 'ice') {
        this._iceChange(subFieldName, newValue)
      } else { this._bidAskChange(fieldName, subFieldName, newValue)};

      this.requestUpdate();
    }

    _bidAskChange(priceType, buySellIndicator, newPrice) {
      let oldPrice = this[priceType][buySellIndicator]; 
      let fieldName = buySellIndicator + '_trend';

      let priceTrend = oldPrice > newPrice ? 'price-down' : oldPrice === newPrice ? 
          '' : 'price-up';
      let currentPriceTrend = this[priceType][fieldName];
      let incomingPriceTrend = priceTrend;

      if (currentPriceTrend === incomingPriceTrend) {
        incomingPriceTrend = priceTrend + '-backup';
      }

      this[priceType][fieldName] = incomingPriceTrend;
      this[priceType][buySellIndicator] = newPrice;
    }

    _iceChange (fieldName, newValue) {
      this.ice[fieldName] = newValue;
      this.ice.shine_class = this.ice.shine_class == 'shine' ? 'shine-backup' : 'shine';
    }
  
     render(){
        return html`
  
        <style>
        :host {
          display: block;
          font-family: monospace;
        }
  
        .container {
          display: flex;
          flex-direction: row;
          justify-content: flex-start;
          align-items: center;
          height: 100%;
          background: #4F759B;
        }

        .title {
          display: inline-block;
          width: 40%;
          text-align: center;
          background: #FFFFF0;
        }
  
        .column {
          display: inline-block;
          height: 100%;
          width: 100%;
        }
  
        </style>
          <div class="container">
            <div class="column">
              <bidask-spread id="bbo" titleLeft="Best Bid" titleRight="Best Ask"
                bid=${this.bbo.bid} bidTrend=${this.bbo.bid_trend} ask=${this.bbo.ask}
                askTrend=${this.bbo.ask_trend}>
              </bidask-spread>
            </div>
            <div class="column">
              <bidask-spread id="mbo" titleLeft="My Bid" titleRight="My Ask"
                bid=${this.mbo.bid} bidTrend=${this.mbo.bid_trend} ask=${this.mbo.ask}
                askTrend=${this.mbo.ask_trend}>
              </bidask-spread>
            </div>
            <div class="column">
              <subject-wallet inventory=${this.ice.inventory} cash=${this.ice.cash}
                endowment=${this.ice.endowment} shineClass=${this.ice.shine_class}> 
              </subject-wallet>
            </div>
          </div>
        `;}
  
  }
  customElements.define('information-table', InfoTable)