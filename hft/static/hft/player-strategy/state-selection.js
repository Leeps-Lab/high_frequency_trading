import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';
import './state-button.js';
import './algorithm-selection.js';
import './speed-selection.js'

class StateSelection extends PolymerElement {
    static get properties() {
        return {
          strategy: {
              type: String,
              observer: '_confirmedStrategyChange',
              value: 'out'
          },
          roles: Object,
          sliderDefaults: Object,
          slider_a_x: {
            type: Number,
            observer: '_sliderValueChange',
            value: 0
          },
          slider_a_y: {
            type: Number,
            observer: '_sliderValueChange',
            value: 0
          }
        }
    }

    static get template() {
        return html`
        <link rel="stylesheet" href="/static/hft/input-section/range.css">
        <style>
            :host {
                display: inline-block;
                font-family: monospace;
                font-weight: bold;
                font-size: 14px;
                height:100%;
                width:100%;
            }
    
            .column-container{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                height: 100%;
                width: 30%;
                margin: 10px;
            }

            .evenly-spaced-column {
                justify-content: space-evenly;
            }

            .header-container {
                background-color: #FFFFF0;
                margin: 5px;
                border-radius: 5%;
                border: 1px solid #000;
                width: 80%;
            }

            .state-container{
                display: flex;
                flex-direction: row;
                justify-content: flex-start;
                align-items: center;
                width:100%;
                height: 100%;
            }

            .slider-header {
                font-size: 12px
            }

            #first-column {
                width: 10%;
            }

            #second-column {
                width: 50%;
                align-items: space-evenly;
            }

        </style>
           
             <div class = "state-container">

                <div id="first-column" class="column-container" >
                    <div class="header-container">
                        Speed
                    </div>
                    <speed-switch 
                    >
                    </speed-switch>
                </div>
                
                <div id="second-column" class="column-container">
                    <div>
                        <state-button
                            strategy="manual"
                            strategy-on = '{{roles.manual}}'
                        >
                        </state-button>

                        <state-button
                            strategy = "maker"
                            strategy-on = '{{roles.maker}}'
                        >
                        </state-button>
                    </div>

                    <div>
                        <state-button
                            strategy="out"
                            strategy-on = '{{roles.out}}'
                        >
                        </state-button>

                        <state-button
                            strategy = "taker"
                            strategy-on = '{{roles.taker}}'
                        >
                        </state-button>
                    </div>
                </div>

                <div class = 'column-container evenly-spaced-column'>
                    <div class="header-container" style="height: 10%">
                        Sensitivities
                    </div>
                    

                    
                    <div class="header-container slider-header">
                        Inventory: {{slider_a_x}}
                    </div>
                    
            
                    <input 
                        class= "slider-group"
                        type="range" 
                        min = '{{sliderDefaults.minValue}}'
                        max = '{{sliderDefaults.maxValue}}'
                        value = '{{slider_a_x::mouseup}}'
                        step = '{{sliderDefaults.stepSize}}'
                    >

                    <div class="header-container slider-header">
                    Imbalance: {{slider_a_y}}
                    </div>

                    <input 
                        type="range" 
                        class="slider-group"
                        min = '[[sliderDefaults.minValue]]'
                        max = '[[sliderDefaults.maxValue]]'
                        value = '{{slider_a_y::mouseup}}'
                        step = '[[sliderDefaults.stepSize]]'
                    >
                </div>
                        
            </div>

        `;
    }

    constructor() {
        super();
    }

    _sliderValueChange(newVal,oldVal){
        let socketMessage = {
            type: "slider",
            a_x: this.slider_a_x,
            a_y: this.slider_a_y
        };
        
        let userInputEvent = new CustomEvent('user-input', {bubbles: true, composed: true, 
            detail: socketMessage });
        
        this.dispatchEvent(userInputEvent);
    }


    _confirmedStrategyChange(newVal , oldVal){
        /*
        To be configurable in markup for true or false 
            the presence of the attribute results in true
            the oposite results to false
            https://polymer-library.polymer-project.org/3.0/docs/devguide/properties#configuring-boolean-properties
        This is undesirable because I want to be able to select
            which state (maker,taker,out,manual) is selected or not
        So in this case I use strings "selected" (true) and "" (false) to represent
            the role being true or false using string comparisons in the 
            components to run actions based on the role being selected or not
        */

        for(var role in this.roles){
            if(role == newVal){
                this.roles[role] = 'selected';
            } else {
                this.roles[role] = 'not-selected';
            }
            this.notifyPath('roles.' + role);
        }
        
        //Below conditional is implementation specific to ELO
        //Only algorithm roles can use the sliders
        let sliders= this.shadowRoot.querySelectorAll('.slider-group')
        sliders.forEach( (element) => { 
            newVal == 'taker' || newVal == 'maker' ? element.disabled = false :
                element.disabled = true }
        )     
    }
  }
  customElements.define('state-selection', StateSelection)