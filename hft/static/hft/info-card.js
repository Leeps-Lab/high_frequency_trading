import { PolymerElement, html } from './node_modules/@polymer/polymer/polymer-element.js';

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
            display: inline-block;
            font-family: monospace;
            }

            .theCard {
            width: 100px;
            height: 40px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            }

            .price-holder {
            display: flex;
            flex-direction: row;
            justify-content: center;
            align-items: center;
            background: #FFFFF0;
            width: 100%;
            border-radius: 5px;
            animation-name: shine;
            animation-duration: 1s;
            animation-timing-function: linear;
            }

            .border {
            border-style: solid;
            border-width: 1px;
            border-color: #black;
            }

            h4 {
            display: inline-block;
            text-align: center;
            background: #FFFFF0;
            width: 80%;
            margin: 0px;
            
            }
            h3 {
            display: inline-block;
            text-align: center;
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
        <div class="theCard">
            <h4> {{title}}</h4>
            <div class="price-holder border" shineClass={{shineClass}}>
            <h3 > {{currency}} {{value}}</h3>
            </div>
        </div>
        `
    }
    }


customElements.define('info-card', InfoCard);