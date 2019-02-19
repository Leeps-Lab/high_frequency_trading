import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';

class SpeedSwitch extends PolymerElement {
    static get template() {
        return html`
        <style>
            :host {
                display: inline-block;
                font-family: monospace;
               
            }
            .switch {
                position: relative;
                display: inline-block;
                width: 60px;
                height: 35px;
              }
              
              .switch #speedCheck { 
                opacity: 0;
                width: 0;
                height: 0;
              }
              
              .slider {
                position: absolute;
                cursor: pointer;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: #ccc;
                -webkit-transition: .4s;
                transition: .4s;
              }
              
              .slider:before {
                position: absolute;
                content: "";
                height: 26px;
                width: 26px;
                left: 4px;
                bottom: 4px;
                background-color: #FFFFF0;
                -webkit-transition: .4s;
                transition: .4s;
              }
              
              #speedCheck:checked + .slider{
                background-color: #008C4F;
              }
              
              #speedCheck:focus + .slider{
                box-shadow: 0 0 1px #2196F3;
              }
              
              #speedCheck:checked + .slider:before {
                -webkit-transform: translateX(26px);
                -ms-transform: translateX(26px);
                transform: translateX(26px);
              }
              
              /* Rounded sliders */
              .slider.round {
                border-radius: 34px;
              }
              
              .container-fluid {
                height: 100%; 
                margin: 0px;
              }
              .slider.round:before {
                border-radius: 50%;
              }
        </style>
        <label class="switch">
                <input id="speedCheck"
                 type="checkbox">
                <span class="slider round"></span>
        </label>
        `
    }

    static get properties(){
        return {
            checked: {
                type: Boolean,
                value: false
            }
        };
    }
        
    constructor(){
        super();  
    }

    ready(){
        super.ready();
        this.$.speedCheck.addEventListener('click', this._updateState.bind(this));
    }

    _updateState(){
        this.checked = !this.checked;

        let socketMessage = {
            type:"speed",
            state: this.checked,
        };
        
        let userInputEvent = new CustomEvent('user-input', {bubbles: true, composed: true, 
            detail: socketMessage });
        
        this.dispatchEvent(userInputEvent);
        //send this.socketMessage over socket

    } 

        
    }
    
customElements.define('speed-switch', SpeedSwitch);