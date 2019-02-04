import { LitElement, html } from '../node_modules/lit-element/lit-element.js';

class StateButton extends LitElement {

    static get properties(){
        return {
        state:{
            type: String
        },
        strategyOn: {
            type: Boolean
        },
        socketMessage: {
            type: String},
        };
    }
        
    constructor(){
        super();
       
        this.socketMessage =  {
            type: "role_change",
            state: this.state
        };

        this.addEventListener('click', this.updateState.bind(this));
    }

    updateState(){
        //send this.socketMessage over socket

        
    } 


    render () {
        return html`
        <style>
            :host {
                display: inline-block;
                font-family: monospace;
            }
        </style>
        <div class="button">
           <button aria-pressed="${this.strategyOn}" >${this.strategy}</button>
        </div>
        `
        }
    }


customElements.define('state-button', StateButton);