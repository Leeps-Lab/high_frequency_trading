import { PolymerElement, html } from '../../node_modules/@polymer/polymer/polymer-element.js';
import {} from '../../node_modules/@polymer/polymer/lib/elements/dom-repeat.js';
import './player-role-button.js'
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
            buttons:Array,
            role:String,
        };
    }
        
    constructor(){
        super(); 
    }
  }
    
customElements.define('buttons-container', ButtonsContainer);