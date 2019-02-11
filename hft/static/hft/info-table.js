import { PolymerElement, html } from './node_modules/@polymer/polymer/polymer-element.js';

class InfoTable extends PolymerElement {
    static get properties() {
      return {
        bestBid: {type: Number},
        bestOffer: {type: Number, value: null},
        myBid: {type: Number, value: null},
        myOffer: {type: Number, value: null},        
        inventory: {type: Number, value: null}, 
        cash: {type: Number, value: null},
        endowment: {type: Object, value: null},
      }
    }
    constructor() {
      super();
    }

    static get template() { 
        return html`
  
        <style>
        :host {
          display: block;
          height: 400px;
          font-family: monospace;
        }
  
        .container {
          display: flex;
          flex-direction: row;
          justify-content: flex-start;
          align-items: center;
          height: 100%;
          width: 100%;
          background: #4F759B;
        }

        .title {
          display: inline-block;
          width: 40%;
          text-align: center;
          background: #FFFFF0;
        }
  
        .row {
          display: inline-block;
          margin: 10px;
          width: 100%;
          height: 100%
        }
  
        </style>
          <div class="container">
            <div class="row">
              <bidask-spread title-left="Best Bid" title-right="Best Ask"
                bid={{bestBid}} ask={{bestOffer}}>
              </bidask-spread>
            </div>
            <div class="row">
              <bidask-spread title-left="My Bid" title-right="My Ask"
                bid={{myBid}} ask={{myOffer}}>
              </bidask-spread>
            </div>
            <div class="row">
              <subject-wallet inventory={{inventory}} cash={{cash}}
                endowment={{endowment}}> 
              </subject-wallet>
            </div>
          </div>
        `;}
  
  }
  customElements.define('info-table', InfoTable)