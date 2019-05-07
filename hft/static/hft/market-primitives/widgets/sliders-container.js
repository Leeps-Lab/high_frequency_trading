import { PolymerElement, html } from '../../node_modules/@polymer/polymer/polymer-element.js';
import {} from '../../node_modules/@polymer/polymer/lib/elements/dom-repeat.js';
import './algorithm-slider.js'
class ButtonsContainer extends PolymerElement {
    //https://polymer-library.polymer-project.org/3.0/api/elements/dom-repeat
    static get template() {
        return html`
        <style>
            :host{
                width:100%;
                height:100%;
            }
        </style>
        <template is="dom-repeat" items="{{buttons}}">
            <player-role-button websocket-message='{"type": "role_change", "state": "[[item]]"}' 
                event-dispatch="user-input"  role-name="[[item]]" player-role=[[role]]>
            </player-role-button>
        </template>   
        `
    }

    static get properties(){
        return {
            sliders:{value:[{
                name: "Inventory",
                minValue: 0,
                maxValue: 4,
                stepSize:0.1
            },
            {
                name: "Signed Volume",
                minValue: 0,
                maxValue: 4,
                stepSize:0.1
            },
            {
                name: "External Feed",
                minValue: 0,
                maxValue: 1,
                stepSize:0.2
            }]},
            role:String,
        };
    }
        
    constructor(){
        super(); 
    }
  }
    
customElements.define('buttons-container', ButtonsContainer);