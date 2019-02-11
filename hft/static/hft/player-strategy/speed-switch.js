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
                width: 100px;
                height: 50px;
                
            }

            .switch input { 
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
                background-color: #7F9AB5;
                -webkit-transition: .4s;
                transition: .4s;
            }

            .slider:before {
                position: absolute;
                content: "";
                height: 42px;
                width: 50px;
                left: 4px;
                bottom: 4px;
                background-color: #FFFFF0;
                -webkit-transition: .2s;
                transition: .2s;
            }

            input:checked + .slider {
                background-color:#008C4F;
            }

            input:focus + .slider {
                box-shadow: 0 0 1px #008C4F;
            }

            input:checked + .slider:before {
                -webkit-transform: translateX(42px);
                -ms-transform: translateX(42px);
                transform: translateX(42px);
            }
            /* Rounded sliders */
            .slider.round {
                border-radius: 20px
            }

            .slider.round:before {
                border-radius: 20px;
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
                type: Boolean
            },
            socketMessage: {
                type: Object
            },
        };
    }
        
    constructor(){
        super();  
        this.socketMessage = {type:"speed"};
    }
    ready(){
        super.ready();
        this.$.speedCheck.addEventListener('click', this.updateState.bind(this));
    }

    updateState(){
   
        this.socketMessage["state"] = this.checked;
        this.checked = !this.checked;

        //send this.socketMessage over socket
        console.log(this.socketMessage);
    } 

        
    }
    
customElements.define('speed-switch', SpeedSwitch);