import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';
import '../market-primitives/widgets/player-role-button.js'
import '../market-primitives/widgets/nice-checkbox.js'

class StateSelection extends PolymerElement {

    static get template() {
        return html`
        <link rel="stylesheet" href="/static/hft/css/range.css">
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
                width: 90%;
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
                    <nice-checkbox is-active={{speedOn}}> </nice-checkbox>
                </div>
                
                <div id="second-column" class="column-container">
                    <div>
                        <player-role-button role-name="manual" player-role=[[role]]>
                        </player-role-button>

                        <player-role-button role-name="maker" player-role=[[role]]>
                        </player-role-button>
                    </div>

                    <div>
                        <player-role-button role-name="out" player-role=[[role]]>
                        </player-role-button>

                        <player-role-button role-name="taker" player-role=[[role]]>
                        </player-role-button>
                    </div>
                </div>

                <div class = 'column-container evenly-spaced-column'>
                    <div class="header-container" style="height: 10%">
                        Sensitivities
                    </div>

                    <div class="header-container slider-header">
                        Inventory: {{slider_a_y}}
                    </div>
                    
            
                    <input class="slider-group" type="range" min='{{sliderDefaults.minValue}}'
                        max='{{sliderDefaults.maxValue}}' value='{{slider_a_y::mouseup}}'
                        step='{{sliderDefaults.stepSize}}'>

                    <div class="header-container slider-header">
                    Imbalance: {{slider_a_x}}
                    </div>

                    <input type="range" class="slider-group" min='[[sliderDefaults.minValue]]'
                        max='[[sliderDefaults.maxValue]]' value='{{slider_a_x::mouseup}}'
                        step='[[sliderDefaults.stepSize]]'>
                </div>
                        
            </div>

        `
    }

    static get properties() {
        return {
          role: {
              type: String,
              observer: '_roleChange',
              value: 'out'
          },
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
          },
          speedOn: {
            type: Boolean, 
            value: false,
            reflectToAttribute: true
            }
        }
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

    _roleChange(newVal , oldVal) {  
        // since I can't set a disabled=true
        // at init time on markup using data binding
        let sliders= this.shadowRoot.querySelectorAll('.slider-group')
        sliders.forEach( (element) => { 
            newVal == 'taker' || newVal == 'maker' ? element.disabled = false :
                element.disabled = true }
        )     
    }
  }
  customElements.define('elo-state-selection', StateSelection)
