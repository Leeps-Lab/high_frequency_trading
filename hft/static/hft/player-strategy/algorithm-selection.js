import { LitElement, html } from 'lit-element';

class AlgorithmSelection extends LitElement {

    static get properties(){
        return {
            makerOn: {
                type: Boolean 
            },
            takerOn: {
                type: Boolean 
            },      
            inventorySensitivyMin: {
                type: Number 
            }, 
            inventorySensitivyMax: {
                type: Number 
            },
            orderSensitivyMin: {
                type: Number 
            },
            orderSensitivityMax: {
                type: Number
            },
            sliderStep: {
                type: Number
            },
            disabledSliders: {
                type: Boolean
            },

        }
    }
        
    constructor(){
        super();
       
        

        
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
            .algorithm-container{
                display: flex;
                flex-direction: row;
                justify-content: flex-start;
                align-items: center;
                height: 100%;
                background: #4F759B;
            }
        </style>
        <div class = "algorithm-container" >
            <div class="column">
                <state-button
                    state="maker"
                    strategyOn = ${this.makerOn}
                >
                </state-button>

                <state-button
                    state="out"
                    strategyOn = ${this.takerOn}
                    
                >
                </state-button>
            </div>
            <div class="column">
                <sensitivity-slider
                    sensitivity="order"
                    disabled = ${this.disabledSliders}
                    min = ${this.orderSensitivyMin}
                    max = ${this.orderSensitivyMax}
                    step = ${this.sliderStep}
                >
                </sensitivity-slider>

                <sensitivity-slider
                    sensitivity="inventory"
                    disabled = ${this.disabledSliders}
                    min = ${this.inventorySensitivyMin}
                    max = ${this.inventorySensitivyMax}
                    step = ${this.sliderStep}
                >
                </sensitivity-slider>
            </div>
        </div>
        
        `
        }
    }


customElements.define('algorithm-selection', AlgorithmSelection);