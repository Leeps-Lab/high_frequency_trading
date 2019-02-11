import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';

class SensitivitySlider extends PolymerElement {
    static get template() {
        return html`
            <link rel="stylesheet" href="/static/hft/input-section/range.css">
            <style>
                :host {
                    display: inline-block;
                    font-family: monospace;
                    width:auto;
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
                    [[sensitivity]]
                </p>
                
                <slider>
                </slider>
                <input 
                    id = 'slider'
                    disabledSlider = "[[disabledSlider]]"
                    type="range" min = "[[min]]" 
                    max = "[[max]]" 
                    value = "0" 
                    step = "[[step]]"
                >
            </div>
        `
    }

    static get properties(){
        return {
            sensitivity: {
                type: String
            },
            disabledSlider: {
                type: String,
                computed: "_slidersDisabled()"
            },
            min: {
                type: Number
            },
            max: {
                type: Number
            },
            step: {
                type: Number
            },
            socketMessage: {
                type: Object
            }
        }
    }
        
    constructor(){
        super();
        this.socketMessage = {type: "slider"};
        
    }

    ready(){
        super.ready();
        console.log(this.$.slider.disabled);
        this.$.slider.addEventListener('mouseup',this.updateState.bind(this));
    }

    updateState(e){

        //send this.socketMessage over socket
        let variable = (this.sensitivity == "Order") ? "a_x" : "a_y";
        this.socketMessage[variable] = parseFloat(e.target.value);
   
        console.log(this.socketMessage);  
    } 
    _slidersDisabled(){
        console.log(this.min);
        if(this.disabledSlider == "selected"){
            this.$.slider.disabled = false;
        } else {
            this.$.slider.disabled = true;
        }
    }


    
    }


customElements.define('sensitivity-slider', SensitivitySlider);