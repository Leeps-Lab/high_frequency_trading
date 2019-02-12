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
                width:100px;
                height:50px;
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
            },
            socketMessage: {
                type: Object
            }
        }
    }
        
    constructor(){
        super();    
        this.socketMessage =  {
            type: "role_change",
        };
        
    }
    ready(){
        super.ready();
        if(this.strategy == "out"){
            this.strategyOn  = "selected";
        } else {
            this.strategyOn  = "";
        }
        
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
        this.socketMessage["state"] = this.strategy;
        //ONLY CHANGE THIS FIELD IF MESSAGE RECIEVED IS ACCEPTED ROLE CHANGE FROM BACKEND TALK TO ALI
        console.log(this.socketMessage);

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