import { PolymerElement, html } from '../../node_modules/@polymer/polymer/polymer-element.js';

class NiceCheckbox extends PolymerElement {
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
              
              .switch #nicecheckbox{ 
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
                background-color: var(--background-color-white);
                -webkit-transition: .4s;
                transition: .4s;
              }
              
              #nicecheckbox[checked] + .slider{
                background-color: #ED6A5A;
              }
              
              #nicecheckbox:focus + .slider{
                box-shadow: 0 0 1px #2196F3;
              }
              
              #nicecheckbox[checked] + .slider:before {
                -webkit-transform: translateX(26px);
                -ms-transform: translateX(26px);
                transform: translateX(26px);
              }

              #nicecheckbox[disabled] + .slider {
                cursor: not-allowed;
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
            <input id="nicecheckbox" checked$=[[isActive]] type="checkbox" on-click="checkboxClicked" disabled$=[[disabled]]>
            <span class="slider round"></span>
        </label>
        `
    }

    static get properties(){
        return {
            isActive: {
              type: Boolean,
              value: false,
              reflectToAtrribute: true,
              observer: '_trigDisableTimer'
            },
            clickable: Boolean,
            disabled: Boolean,
            websocketMessage: Object,
            eventDispatch: String,
            expiryDuration: Number //ms
            // isChecked: {
            //   type: Boolean,
            //   reflectToAtrribute: true,
            // },
        };
    }
        
    constructor(){
        super();  
        this.clickable = true
        this.expiryDuration = 4000;
    }

    _trigDisableTimer(newValue, oldValue){
      if (newValue){
        this.clickable = false
        setTimeout(() => {this.clickable = true}, this.expiryDuration)
      }
    }

    checkboxClicked(event) {
      event.preventDefault();
      if (this.clickable || !this.isActive) {
        this.websocketMessage["value"] = !this.isActive;    
        let userInputEvent = new CustomEvent(this.eventDispatch, {bubbles: true, 
          composed: true, detail: this.websocketMessage });   
        this.dispatchEvent(userInputEvent);
    }
  }
}
    
customElements.define('nice-checkbox', NiceCheckbox);