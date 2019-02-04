import { LitElement, html } from '../node_modules/lit-element/lit-element.js';

class SensitvitySlider extends LitElement {

    static get properties(){
        return {
            sensitivity: {
                type: String
            },
            disabled: {
                type: Boolean
            },
            min: {
                type: Number
            },
            max: {
                type: Number
            },
            step: {
                type: Number
            }
      
        }
    }
        
    constructor(){
        super();
    

        this.addEventListener('click', this.updateState.bind(this));
    }

    updateState(){
        //send this.socketMessage over socket

        
    } 


    render () {
        return html`
        <style>
            :host {
                display: inline-block;
                font-family: monospace;
            }
        </style>
        <div class="slider-container">
            <h2>
                ${this.senstivity}
            </h2>
            <input 
                type="range" min = "${this.min}" 
                max = "${this.max}" 
                value="0" 
                step="${this.step}"
            >
        </div>
        `
        }
    }


customElements.define('sensitvity-slider', SensitvitySlider);