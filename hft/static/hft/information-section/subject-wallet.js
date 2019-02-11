import { LitElement, html } from '../node_modules/lit-element/lit-element.js';

class WallletCard extends LitElement {

    static get properties(){
      return {
        title: {type: String},
        contentBottom: {type: String},
        shineClass: {type: String},
        inventory: {type: Number},
        cash: {type: Number},
        endowment: {type: Number}
      };
    }
  
    constructor(){
      super();
      this.shineClass = '';
      this.inventory = 0;
      this.cash = 0;
      this.endowment = 0;
    }
  
    render() {
      return html`  
        <style>
          :host {
            display: inline-block;
            font-family: monospace;
            width: 100%;
            height: 100%;
          }
          .container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
          }
        </style>

        <div class="container"> 
          <info-card class="thecard" title="Inventory" currency="" value=${this.inventory}
            shineClass=${this.shineClass}></info-card>
          <info-card class="thecard" title="Cash" currency="$" value=${this.cash}
            shineClass=${this.shineClass}></info-card>
          <info-card class="thecard" title="Cash + p*Q" currency="$" value=${this.endowment}
            shineClass=${this.shineClass}></info-card>
        </div>
        `;
    }
  }  
  
customElements.define('subject-wallet', WallletCard);
