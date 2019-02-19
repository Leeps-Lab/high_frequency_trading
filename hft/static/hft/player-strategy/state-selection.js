import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';
import './state-button.js';
import './algorithm-selection.js';
import './speed-selection.js'

class StateSelection extends PolymerElement {
    static get properties() {
        return {
          strategy: {
              type: String,
              observer: '_confirmedStrategyChange'
          },
          roles: {
              type: Object
          },
          disabledSliders:{
              type: String
          },
        }
    }

    static get template() {
        return html`
        <style>
            :host {
                display: inline-block;
                font-family: monospace;
                height:100%;
                width:100%;
                background: #4F759B;
            }
    
            .title-container{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }
            .state-container{
                display: flex;
                flex-direction: row;
                justify-content: flex-start;
                align-items: center;
                /* height:200px; */
                width:100%;
            }
            .column {
                display: inline-block;
                height: 100%;
                width: 100%;
            }

            .button-container{
                display: flex;
                flex-direction: column;
                justify-content: baseline;
                align-items: center;
            }
            .algorithm{
                width:50%;
            }
    
            .speed-basic-container{
                display: flex;
                flex-direction: row;
                justify-content: center;
                align-items: center;
                width:50%;
            }
            p{
                text-align: center;
                font-weight:bold;
                font-size:14px;
                background: #FFFFF0;
                width:50%;
            }
        </style>

            
            
             <div class = "state-container">

                <div class = 'column-container speed-switch'>
                    <p>
                        Speed
                    </p>
                    <speed-switch 
                    >
                    </speed-switch>
                </div>
                
                <div class = 'column-container button-container'>
                    <state-button
                    strategy='manual'
                    strategy-on = '{{roles.manual}}'
                    >
                    </state-button>

                    <state-button
                        strategy="out"
                        strategy-on = '{{roles.out}}'
                    >
                    </state-button>

                    <state-button
                        strategy = "maker"
                        strategy-on = '{{roles.maker}}'
                    >
                    </state-button>

                    <state-button
                        strategy = "taker"
                        strategy-on = '{{roles.taker}}'
                    >
                    </state-button>
                </div>

                <div class = 'column-container'>
                    <p>
                        Sensitivities
                    </p>
                    <hr style = 'width:90%;'>
                    <sensitivity-slider
                    sensitivity = "Order"
                    disabled-slider = '{{disabledSliders}}'
                    min = "0"
                    max = "10"
                    step = "0.1"
                    >
                    </sensitivity-slider>

                    <sensitivity-slider
                        sensitivity = "Inventory"
                        disabled-slider = '{{disabledSliders}}'
                        min = "0"
                        max = "10"
                        step = "0.1"
                    >
                    </sensitivity-slider>
                </div>
                        
            </div>

        `;
    }

    constructor() {
        super();
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
        
        for(let role in this.roles){
            if(role == newVal){
                this.roles[role] = 'selected';
            } else {
                this.roles[role] = 'not-selected';
            }

            //Absolutely necessary line below to 
            //notfiy the roles object in markup (html) to change
            this.notifyPath('roles.' + role);

            //Below conditional is implementation specific to ELO
            //Only algorithm roles can use the sliders
            if(newVal == 'taker' || newVal == 'maker'){
                this.disabledSliders = 'selected';
            } else { 
                this.disabledSliders = 'not-selected';
            }
        }

    }
  }
  customElements.define('state-selection', StateSelection)