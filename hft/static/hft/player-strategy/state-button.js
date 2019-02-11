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
            >[[strategy]]</button>
        </div>
        `;
    }
    static get properties(){
        return {
            strategy:{
                type: String
            },
            strategyon: {
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
            this.strategyon  = "selected";
        } else {
            this.strategyon  = "";
        }
        
        this.$.stateButton.addEventListener('click', this.updateState.bind(this));
        

    }

    _buttonOn(){
       
      if(this.strategyon == "selected"){
        this.$.stateButton.className = 'role-selected';
      } else {
        this.$.stateButton.className = '';
      }
    }

    updateState(){
        this.socketMessage["state"] = this.strategy;
        //send this.socketMessage over socket
        
        
        //ONLY CHANGE THIS FIELD IF MESSAGE RECIEVED IS ACCEPTED ROLE CHANGE FROM BACKEND TALK TO ALI
        if(this.strategyon == "selected"){
            this.strategyon = "";
        } else {
            this.strategyon = "selected";
        }
        console.log(this.socketMessage);

    } 


    
    }


customElements.define('state-button', StateButton);