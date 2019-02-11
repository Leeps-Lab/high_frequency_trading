import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';

import './state-button.js';
import './sensitivity-slider.js';
import './speed-selection.js';

class AlgorithmSelection extends PolymerElement {
    static get template() {
        return html`
        <style>
            :host {
                display: inline-block;
                height: 100%;
                width: 100%;
                font-family: monospace;
            }

            .title-container{
                width:100%;
                display: flex;
                display: inline-block;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }

            .top-title{
                text-align: center;
                background: #FFFFF0;
            }

            .algorithm-selection-container{
                display: flex;
                flex-direction: row;
                justify-content: flex-start;
                align-items: center;
                border-left: 1px solid #FFFFF0;
            }
            
            .algorithm-buttons{
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                align-items: center;
                width:50%;
            }

            .sliders{
                width:50%;
                height:100%;
            }

            p{
                text-align: center;
                font-weight:bold;
                font-size:14px;
                background: #FFFFF0;
              
            }
        </style>

     
            <div class = "algorithm-selection-container">
                <div class="column algorithm-buttons">
 
                        <state-button
                            strategy="maker"
                            strategyOn = "[[makerOn]]"
                        >
                        </state-button>

                        <state-button
                            strategy="taker"
                            strategyOn = "[[takerOn]] " 
                        >
                        </state-button>
          
                </div>

                <div class="column sliders">
                    
                    <sensitivity-slider
                        sensitivity="Order"
                        disabledSlider ="[[disabledSliders]]"
                        min = "0"
                        max = "10"
                        step = "0.1"
                    >
                    </sensitivity-slider>

                    <sensitivity-slider
                        sensitivity="Inventory"
                        disabledSlider = "[[disabledSliders]]"
                        min = "0"
                        max = "10"
                        step = "0.1"
                    >
                    </sensitivity-slider>
                    
                </div>
            </div>
        `;

    }
    static get properties(){
        return {
            makeron: {
                type: String,
                computed: '_algorithmRoleSelected()' 
            },
            takeron: {
                type: String,
                computed: '_algorithmRoleSelected()' 
            },      
            inventorySensitivityMin: {
                type: Number 
            }, 
            inventorySensitivityMax: {
                type: Number 
            },
            orderSensitivityMin: {
                type: Number 
            },
            orderSensitivityMax: {
                type: Number
            },
            sliderStep: {
                type: Number
            },
            disabledSliders: {
                type: String
            },

        }
    }
        
    constructor(){
        super();

    }


    updateState(){
        //send this.socketMessage over socket

        
    } 
    _algorithmRoleSelected(){
        if(this.takerOn == "selected" || this.makerOn == "selected"){
            this.disabledSliders = "selected";
        } else {
            this.disabledSliders = "";
        }

    }


    }


customElements.define('algorithm-selection', AlgorithmSelection);