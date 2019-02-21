import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';
import './speed-switch.js'

class SpeedSelection extends PolymerElement {
    static get template() {
        return html`
        <style>
            :host {
                display: inline-block;
                font-family: monospace;
                height:100%;
                width:100%;
            }

            .speed-container{
                width:100%;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                align-items: center;
            }
        </style>

        <div class = "speed-container">
            <p>
                [[title]]
            </p>

            
            
        </div>
        `
    };
    
    static get properties(){
        return {
            title:{
                type: String
            },

        };
    }
        
    constructor(){
        super();
    }

    
    }


customElements.define('speed-selection', SpeedSelection);