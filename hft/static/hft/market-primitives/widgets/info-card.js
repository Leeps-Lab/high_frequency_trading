import { PolymerElement, html } from '../../node_modules/@polymer/polymer/polymer-element.js';

class InfoCard extends PolymerElement {

    static get properties(){
        return {
        title: String,
        value: {type: Number, observer: '_makeMeShine'},
        currency: String,
        shineClass: String
        };
    }
        
    constructor(){
        //Can't this be intialized in markup where this is used?
        //Are these needed? They are initialized in markup
        super();
        this.title = '#title';
        this.value = 0;
        this.currency = '#currency';
        this.shineClass = '';
        }  
    
    _makeMeShine (newValue, oldValue) {
        this.shine_class = this.shine_class == 'shine' ? 'shine-copy' : 'shine';
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
              animation-name: shine;
              animation-duration: 1s;
              animation-timing-function: linear;
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
              margin:0px 10px 0px 0px;
            }

            [shineclass=shine-copy] {
                animation-name: shine-more;
                animation-duration: 0.6s;
                animation-timing-function: ease-out;
            }
    
            [shineclass=shine] {
                animation-name: shine;
                animation-duration: 0.7s;
                animation-timing-function: ease-out;
              }
    
              @keyframes shine{
                100% {
                  background-color: #ECE2D0;
                };     
              }
    
              @keyframes shine-more {
                100% {
                  background-color: #ECE2D0;
                };
              }
        </style>
        <div class="theCard border">
            <h4> {{title}}: </h4>
            <div class="price-holder" shineClass={{shineClass}}>
            <h3 > {{currency}} {{value}}</h3>
            </div>
        </div>
        `
    }
    }


customElements.define('info-card', InfoCard);