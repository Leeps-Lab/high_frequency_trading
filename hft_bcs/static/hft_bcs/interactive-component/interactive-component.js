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


    this.startInteractiveComponent();


  }


    startInteractiveComponent(){
     



    }



  }

window.customElements.define('interactive-component', InteractiveComponent);
