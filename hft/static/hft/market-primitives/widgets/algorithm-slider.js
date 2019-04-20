import { PolymerElement, html } from '../../node_modules/@polymer/polymer/polymer-element.js';

class algorithmSlider extends PolymerElement {

    static get template() {
        return html`
        <link rel="stylesheet" href="/static/hft/css/range.css">
        <style>
            :host {
                display: inline-block;
                font-family: monospace;
                font-weight: bold;
            }
            .header-container {
                background-color: #FFFFF0;
                margin: 5px;
                border-radius: 5%;
                border: 1px solid #000;
                width: 90%;
            }
            .slider-header {
                font-size: 12px
            }
        </style>

        <div class="header-container slider-header">
            [[sliderName]]: [[val]]
        </div>
        <input type="range" class="slider-group" min='[[minValue]]'
            max='[[maxValue]]' value='{{val::mouseup}}'
            step='[[stepSize]]' disabled$=[[isDisabled]]>
        `;
    }

    static get properties(){
        return {
            sliderName:String,
            stepSize:Number,
            maxValue:Number,
            minValue:Number,
            val:Number,
            isDisabled:{
                type: Boolean,
                observer: '_resetVal'
            },
        }
    }
    constructor(){
        super();    
    }

    _resetVal(newVal, oldVal){
        //reseting the value of the sliders when
        //the sliders are enabled
        if(newVal == false){this.val = 0;}
    }
}

customElements.define('algorithm-slider', algorithmSlider);