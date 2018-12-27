import {html,PolymerElement}   from '../node_modules/@polymer/polymer/polymer-element.js';

/**
 * @customElement
 * @polymer
 */
class InteractiveComponent extends PolymerElement {
  constructor() {
    super();
    //First we access the shadow dom object were working with
    interactiveComponent.interactiveComponentShadowDOM = document.querySelector("interactive-component").shadowRoot;
    //Second we add the HTML neccessary to be manipulated in the constructor and the subsequent functions
    interactiveComponent.interactiveComponentShadowDOM.innerHTML = `

  <spread-graph></spread-graph>

  <div class="button-container">
      <input-section></input-section>
  </div>
  `;
  interactiveComponent.updateOrders = this.updateOrders;

  }

  updateOrders(msg){
    //filter order message
    //At playersInMarket[playerId]
      /*
        - update the order 
        - update price
        - update type
      */

    //At visibileticklines[price]
      /*
        - Add order to the queue
      */

      

  }


}

window.customElements.define('interactive-component', InteractiveComponent);
