import { PolymerElement, html } from '../../node_modules/@polymer/polymer/polymer-element.js';

class InfoCard extends PolymerElement {

    static get properties(){
        return {
        title: String,
        value: {type: Number, observer: '_makeMeShine'},
        animated: Boolean,
        currency: String,
        shineClass: String
        }
    }
        
    constructor(){
        super();
        this.title = '#title';
        this.value = 0;
        this.currency = '#currency';
        this.shineClass = '';
        }  

    _makeMeShine (newValue, oldValue) {
        if (this.animated) {
          let priceHolder = this.shadowRoot.querySelector('.price-holder')
          this.shineClass = this.shineClass == 'shine' ? 'shine-copy' : 'shine'
          // interestingly polymer data binding did not reflect to dom somehow
          priceHolder.setAttribute("shine-class", this.shineClass)
        }
    }

    static get template() {
        return html`
        <style>
            :host {
              font-family: monospace;
              width:100%;
            }

            .theCard {
              display: flex;
              background: #FFFFF0;
              align-items: center;
            }

            .price-holder {
              text-align: right;
              width: 100%;
              height:30px;
            }

            .border {
              border-radius: 5px;
            }

            h4 {
              margin: 0px 0px 0px 10px;
            }
            h3 {
              display: inline-block;
              text-align: center;
              margin: 0px 0px 0px 10px;
            }

            [shine-class=shine-copy] {
                animation-name: shine-more;
                animation-duration: 0.15s;
                animation-timing-function: ease-in-out;
                animation-iteration-count: 3;
            }
    
            [shine-class=shine] {
                animation-name: shine;
                animation-duration: 0.15s;
                animation-timing-function: ease-in-out;
                animation-iteration-count: 3;
              }
    
              @keyframes shine{
                100% {
                  background-color: #F26419
                  };    
              }
    
              @keyframes shine-more {
                100% {
                  background-color: #F26419
                  };
                  10% {
                  background-color: #F26419
                  };
              }
        </style>
        <div class="theCard border">
            <h4> {{title}}: </h4>
            <div class="price-holder border" shine-class={{shineClass}}>
            <h3 > {{currency}} {{value}}</h3>
            </div>
        </div>
        `
    }
    }


customElements.define('info-card', InfoCard);