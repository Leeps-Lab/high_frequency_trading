import { LitElement, html } from '../node_modules/lit-element/lit-element.js';

class InfoCard extends LitElement {

    static get properties(){
        return {
        title: {type: String},
        value: {type: Number},
        currency: {type: String},
        shineClass: {type: String}
        };
    }
        
    constructor(){
        super();
        this.title = '#title';
        this.value = 0;
        this.currency = '#currency';
        this.shineClass = '';
        }  

        updated(changed) {
            console.log('info card changed', this.value);
        } 

    render () {
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

            [shineclass=shine-backup] {
                animation-name: shine-more;
                animation-duration: 0.6s;
                animation-timing-function: ease-in-out;
              }
    
            [shineclass=shine] {
                animation-name: shine;
                animation-duration: 0.7s;
                animation-timing-function: ease-in-out;
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
            <h4> ${this.title}</h4>
            <div class="price-holder border" shineClass=${this.shineClass}>
            <h3 > ${this.currency} ${this.value}</h3>
            </div>
        </div>
        `
    }
    }


customElements.define('info-card', InfoCard);