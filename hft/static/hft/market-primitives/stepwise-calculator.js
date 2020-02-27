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
            lastStep: {type: Number, notify: true,
              reflectToAttribute: true},
            sleepDuration: {
              type: Number,
              value: 1000
            },
            runForever: {
              type: Boolean, 
              value: false,
              observer: '_run'
            }
        };
    }

    stop() {
      clearInterval(this.intervalId);
    }
    
    _run (newValue, oldValue) {     
      if (newValue) {
        this.lastCalcTime = Date.now()
        this.intervalId = setInterval(() => {
            if (this.runForever) {
              let now = Date.now() 
              let step = (now - this.lastCalcTime) * this.unitSize
              this.lastCalcTime = now
              this.value += step
            }}, 
          this.sleepDuration)
        }
    }
}


customElements.define('stepwise-calculator', StepwiseCalculator);