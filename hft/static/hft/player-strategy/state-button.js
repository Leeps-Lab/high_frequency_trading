import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';

class StateButton extends PolymerElement {

    static get properties(){
        return {
            strategy:{
                type: String
            },
            strategyOn: {
                type: String,
                observer:'_buttonOn'
            }
        }
    }

    static get template() {
        return html`
        <style>
            :host {
                display: inline-block;
                font-family: monospace;
                font-weight: bold;
            }

            button{
                font-family: monospace;
                font-size: 16px;
                background-color:#7F9AB5;
                color:#FFFFF0;
                text-align:center;
                width:90px;
                height:45px;
                border-radius: 5px;
                margin-top:10px;
            }

            .role-selected{
                animation-name: colorful;
                animation-color: 4s;

            }

            @keyframes colorful {
                100% {
                  background-color: #ED6A5A;
                }
            
        </style>
        <div class="button">
            <button
                id="stateButton"
                on-click="_handleClick"
                class = ""
            > {{strategy}} </button>
        </div>
        `;
    }
        
    constructor(){
        super();    
    }

    // ready(){
    //     super.ready();

    //     // this.$.stateButton.addEventListener('click', this._pendingState.bind(this));
        
    // }

    _handleClick(){
        let socketMessage = {
            type: 'role_change',
            state: this.strategy,
        }

        let userInputEvent = new CustomEvent('user-input', {bubbles: true, composed: true, 
            detail: socketMessage });
            
        this.dispatchEvent(userInputEvent);
    } 

    _buttonOn(newVal, oldVal){
        if(newVal == 'selected'){
            this.$.stateButton.className = 'role-selected';
        } else {
            this.$.stateButton.className = '';
        }
    }



    // _confirmState(event){
    //     console.log(event);
    //     let strategy = event.detail.state;
    //     if(strategy == this.strategy){
    //         this.strategyOn = "selected";
    //     } else {
    //         this.strategyOn = "";
    //     }
    // }

}

customElements.define('state-button', StateButton);