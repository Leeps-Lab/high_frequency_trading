import { PolymerElement, html } from '../node_modules/@polymer/polymer/polymer-element.js';

class StepwiseCalculator extends PolymerElement {

    static get properties(){
        return {
            value: {
              type: Number, 
              value: 0,
              notify: true,
              reflectToAttribute: true
          },
            unitSize: Number,
            lastCalcTime: Number,
            sleepDuration: {
              type: Number,
              value: 2000
            },
            runForever: {
              type: Boolean, 
              value: false,
              observer: '_run'
            }
        };
    }
        
    constructor(){
        super();
    }  
    
    _run (newValue, oldValue) {     
      if (newValue) {
        this.lastCalcTime = Date.now()
        setInterval(() => {
            if (this.runForever) {
              let now = Date.now() 
              let step = (now - this.lastCalcTime) * this.unitSize
              this.lastCalcTime = now
              this.value += step
              }}, 
          this.sleepDuration)
        }
    }

    static get template() {return html``}
    }


customElements.define('stepwise-calculator', StepwiseCalculator);