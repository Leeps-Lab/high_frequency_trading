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
          maker:{
              type: String
          },
          taker:{
              type: String
          },
          manual:{
              type: String
          },
          out:{
              type: String
          },
          disabledSliders:{
              type: String
          }
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


        </style>
            
             <div class = "state-container">
                    <div class = "speed-basic-container">
        
                        <div class = "column speed-switch">

                            <speed-selection
                                title = "Speed"
                            >
                            </speed-selection>
                        
                        </div>
                        <div class="column button-container">

                            <state-button
                                strategy="manual"
                                strategy-on = '{{manual}}'
                            >
                            </state-button>
            
                            <state-button
                                strategy="out"
                                strategy-on = '{{out}}'
                            >
                            </state-button>

                        </div>
                    </div>

                <div class="column algorithm">
                    <algorithm-selection 
                         disabled-sliders = '{{disabledSliders}}'
                         maker-on = '{{maker}}'
                         taker-on = '{{taker}}'
                    >
                    </algorithm-selection>
                    
                </div>
            </div>

        `;
    }



    constructor() {
        super();
    }

    ready(){
        super.ready();

        if(this.strategy == 'out'){
            this.outState = 'selected';
        }
        console.log(this.strategy);

    }

    _confirmedStrategyChange(newVal , oldVal){
        console.log('Shit' , newVal);

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
        if (newVal == 'out'){

            this.out = 'selected';
            this.maker = 'not-selected';
            this.taker = 'not-selected';
            this.manual = 'not-selected';

            this.disabledSliders = 'not-selected';

        } else if (newVal == 'manual'){

            this.manual = 'selected';
            this.out = 'not-selected';
            this.maker = 'not-selected';
            this.taker = 'not-selected';

            this.disabledSliders = 'not-selected';

        } else if (newVal == 'maker'){

            this.maker = 'selected';
            this.out = 'not-selected';
            this.taker = 'not-selected';
            this.manual = 'not-selected';

            this.disabledSliders = 'selected';

        } else if (newVal == 'taker'){
            this.taker = 'selected';
            this.out = 'not-selected';
            this.maker = 'not-selected';
            this.manual = 'not-selected';

            this.disabledSliders = 'selected';
        }

    }
  

 
  
  }
  customElements.define('state-selection', StateSelection)