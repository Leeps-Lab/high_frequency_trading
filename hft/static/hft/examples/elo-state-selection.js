import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';
import {} from '../node_modules/@polymer/polymer/lib/elements/dom-if.js';
import '../market-primitives/widgets/player-role-button.js'
import '../market-primitives/widgets/nice-checkbox.js'
import '../market-primitives/widgets/algorithm-slider.js'

class StateSelection extends PolymerElement {
     //dom-repeat
     //https://polymer-library.polymer-project.org/3.0/api/elements/dom-repeat
    static get template() {
        return html`
        <link rel="stylesheet" href="/static/hft/css/range.css">
        <style>
            :host {
                display: inline-block;
                font-family: monospace;
                font-weight: bold;
                font-size: 14px;
            }
    
            .column-container{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                height: 100%;
                width: 55%;
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
                width: 5%;
            }

            #second-column {
                width: 40%;
                align-items: left;
            }

        </style>
        
             <div class = "state-container">

                <div id="first-column" class="column-container" >
                    <div class="header-container">
                        Speed
                    </div>
                    <nice-checkbox websocket-message='{"type": "speed_change"}' 
                        event-dispatch="user-input" is-active={{speedOn}}> </nice-checkbox>
                </div>
                
                <div id="second-column" class="column-container">
                    <player-role-button websocket-message='{"type": "role_change", "state": "out"}' 
                            event-dispatch="user-input"  role-name="out" player-role=[[role]]>
                    </player-role-button>

                    <template is="dom-if" if="{{manualButtonDisplayed}}">
                        <player-role-button websocket-message='{"type": "role_change", "state": "manual"}' 
                                event-dispatch="user-input"  role-name="manual" player-role=[[role]]>
                        </player-role-button>
                    </template>  
                    
                    <player-role-button websocket-message='{"type": "role_change", "state": "automated"}' 
                            event-dispatch="user-input"  role-name="automated" player-role=[[role]]>
                    </player-role-button>
                </div>
                
                <div class = 'column-container evenly-spaced-column'>
                    <div class="header-container" style="height: 10%">
                        Sensitivity to:
                    </div>
                    <algorithm-slider max-value='[[sliderDefaults.maxValue]]' min='[[sliderDefaults.minValue]]'
                        slider-value='{{slider_a_x}}' slider-name="Inventory" step-size='[[sliderDefaults.stepSize]]'>
                    </algorithm-slider>

                    <template is="dom-if" if="{{svSliderDisplayed}}">
                        <algorithm-slider max-value='[[sliderDefaults.maxValue]]' 
                            min='[[sliderDefaults.minValue]]' slider-value='{{slider_a_y}}' 
                            slider-name="Signed Volume" step-size='[[sliderDefaults.stepSize]]'
                            is-disabled="true">
                        </algorithm-slider>
                    </template>

                    <algorithm-slider max-value='1' min='0'
                        slider-value='{{slider_a_z}}' slider-name="External Feed" step-size='0.2'>
                    </algorithm-slider>     
                    
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
          manualButtonDisplayed: {
              type: Boolean,
            //   value: true
          },
          svSliderDisplayed:  {
            type: Boolean,
            // value: true
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
          slider_a_z: {
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
            a_y: this.slider_a_y,
            a_z: this.slider_a_z
        };
       
        let userInputEvent = new CustomEvent('user-input', {bubbles: true, composed: true, 
            detail: socketMessage });
        this.dispatchEvent(userInputEvent);
    }

    _roleChange(newVal , oldVal) {  
        let sliders = this.shadowRoot.querySelectorAll('algorithm-slider')
        sliders.forEach( (element) => { 
            newVal != 'automated' ? element.isDisabled = true :
            element.isDisabled = false }
        )     
    }
  }
  customElements.define('elo-state-selection', StateSelection)
