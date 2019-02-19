import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';

class StateButton extends PolymerElement {
    static get template() {
        return html`
        <style>
            :host {
                display: inline-block;
                font-family: monospace;
            }

            button{
                font-family: monospace;
                background-color:#7F9AB5;
                color:#FFFFF0;
                font-size:20px;
                text-align:center;
                width:90px;
                height:45px;
                border-radius: 6px;
                margin-top:10px;
            }

            button:active{  
                background-color:#42607F;
            }

            .role-selected{
                background-color:#008C4F;
            }
        </style>
        <div class="button">
            <button
                id = 'stateButton'
                class = ""
            >{{strategy}}</button>
        </div>
        `;
    }
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
        
    constructor(){
        super();    
    }
    ready(){
        super.ready();

        this.$.stateButton.addEventListener('click', this._pendingState.bind(this));
        
    }


    _buttonOn(newVal, oldVal){
        if(newVal == 'selected'){
            this.$.stateButton.className = 'role-selected';
        } else {
            this.$.stateButton.className = '';
        }
    }


    _pendingState(){
        let socketMessage = {
            type: 'role_change',
            state: this.strategy,
        }

        let userInputEvent = new CustomEvent('user-input', {bubbles: true, composed: true, 
            detail: socketMessage });
            
        this.dispatchEvent(userInputEvent);
    } 

    _confirmState(event){
        console.log(event);
        let strategy = event.detail.state;
        if(strategy == this.strategy){
            this.strategyOn = "selected";
        } else {
            this.strategyOn = "";
        }
    }

}

customElements.define('state-button', StateButton);