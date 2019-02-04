import { LitElement, html } from '../node_modules/lit-element/lit-element.js';

class StateSelection extends LitElement {

    static get properties() {
      return {
        title:{
            type: String
        },
        manualState: {
            type: Boolean
        },
        makerState: {
            type: Boolean
        },
        takerState: {
            type: Boolean
        },
        outState: {
            type: Boolean
        },
        speedState: {
            type: Boolean
        },
      }
    }

    constructor() {
        super();
        this.speed = false;
      
    }
  
    updateState(fieldName, subFieldName, newValue) {
      // the single entry point for info table

      if (fieldName == 'ice') {
        this._iceChange(subFieldName, newValue)
      } else { this._bidAskChange(fieldName, subFieldName, newValue)};

      this.requestUpdate();
    }

    // _bidAskChange(priceType, buySellIndicator, newPrice) {
    //   let oldPrice = this[priceType][buySellIndicator]; 
    //   let fieldName = buySellIndicator + '_trend';

    //   let priceTrend = oldPrice > newPrice ? 'price-down' : oldPrice === newPrice ? 
    //       '' : 'price-up';
    //   let currentPriceTrend = this[priceType][fieldName];
    //   let incomingPriceTrend = priceTrend;

    //   if (currentPriceTrend === incomingPriceTrend) {
    //     incomingPriceTrend = priceTrend + '-backup';
    //   }

    //   this[priceType][fieldName] = incomingPriceTrend;
    //   this[priceType][buySellIndicator] = newPrice;
    // }

    // _iceChange (fieldName, newValue) {
    //   this.ice[fieldName] = newValue;
    //   this.ice.shine_class = this.ice.shine_class == 'shine' ? 'shine-backup' : 'shine';
    // }
  
     render(){
        return html`
        <style>
            :host {
            display: block;
            font-family: monospace;
            height:100%;
            width:100%;
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
            .top-title{
                display: inline-block;
                width: 40%;
                text-align: center;
                background: #FFFFF0;
            }
        </style>

          <div class="container">
      
            <h2 class = "top-title">
                ${this.title}
            </h2>
            
            <div class="column">
              <state-button
                state="manual"
                strategyOn = ${this.manualState}
              >
              </state-button>
              
              <state-button
                state="out"
                strategyOn = ${this.outState}
                
              >
              </state-button>
            </div>
            <div class="column">
                <algorithm-selection 
                    makerOn = ${this.makerState}
                    takerOn = ${this.takerState}
                    inventorySensitivyMin = 0
                    inventorySensitivyMax = 10 
                    orderSensitivyMin = 0
                    orderSensitivyMax = 10
                    sliderStep = 0.1
                >
                </algorithm-selection>
                
            </div>
          </div>
        `;}
  
  }
  customElements.define('state-selection', StateSelection)