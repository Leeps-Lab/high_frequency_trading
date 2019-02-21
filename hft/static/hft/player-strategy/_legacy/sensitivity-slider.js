import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';

class SensitivitySlider extends PolymerElement {
    static get template() {
        return html`
            <link rel="stylesheet" href="/static/hft/input-section/range.css">
            <style>
                :host {
                    display: inline-block;
                    font-family: monospace;
                    width:80%;
                }
                p{
                    text-align: center;
                    font-weight:bold;
                    font-size:14px;
                    background: #FFFFF0;
                }
            </style>
            <div class="slider-container">
                <p>
                    {{sensitivity}}: <span id='output'></span>
                </p>
                
           
                <input 
                    id = 'slider'
                    type="range" min = '{{min}}'
                    max = '{{max}}'
                    value = '0' 
                    step = '{{step}}'
                >
            </div>
        `;
    }

    static get properties(){
        return {
            sensitivity: {
                type: String
            },
            disabledSlider: {
                type: String,
                observer: "_slidersDisabled"
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
    }

    ready(){
        super.ready();
    
        this.$.slider.addEventListener('mouseup',this._sendValues.bind(this));
           
        let sens = this.$.slider;
        let sensOutput = this.$.output;
      
        sensOutput.innerHTML = sens.value;
    
        sens.oninput = function() {
            sensOutput.innerHTML = this.value;
        }
        

    }

    _sendValues(e){

        let socketMessage = {
            type:"slider",
            title: this.sensitivity,
            value: parseFloat(e.target.value)
        };
        
        let userInputEvent = new CustomEvent('user-input', {bubbles: true, composed: true, 
            detail: socketMessage });
        
        this.dispatchEvent(userInputEvent);
    } 

    _slidersDisabled(newVal , oldVal){
        if(newVal == 'selected'){
            this.$.slider.disabled = false;
        } else if(newVal == 'not-selected'){
            this.$.slider.disabled = true;
        } else {
            console.error('newVal not recognized ' + newVal);
        }
    }


    
    }


customElements.define('sensitivity-slider', SensitivitySlider);