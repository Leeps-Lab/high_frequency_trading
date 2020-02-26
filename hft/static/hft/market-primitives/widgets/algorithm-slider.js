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
                width: 85%;
            }
            .header-container {
                background-color: var(--background-color-white);
                margin: 5px;
                border-radius: 5%;
                border: 1px solid #000;
            }
        </style>

        <div class="header-container slider-header">
            [[sliderName]]: [[sliderValue]]
        </div>
        <input style="background-color:{{color}};" type="range" class="slider-group" min='[[minValue]]'
            max='[[maxValue]]' value='{{sliderValue::mouseup}}'
            step='[[stepSize]]' disabled$=[[isDisabled]] id="slider">
        `;
    }

    static get properties(){
        return {
            sliderName:String,
            stepSize:Number,
            maxValue:Number,
            minValue:Number,
            color:String,
            sliderValue:{
                type: Number,
                reflectToAttribute: true,
                notify: true,
            },
            isDisabled:{
                type: Boolean,
                observer: '_resetVal'
            },
        }
    }

    ready() {
        super.ready();
        this.$.slider.value=this.sliderValue; 
    }

    _resetVal(newVal, oldVal){
        //reseting the value of the sliders when
        //the sliders are enabled
        if(newVal == false){this.val = 0;}
    }
}

customElements.define('algorithm-slider', algorithmSlider);