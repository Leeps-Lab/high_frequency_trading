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
  <style>
  .button-container{
    background-color: rgb(200, 200, 200);
    padding-bottom: 5px;
    flex: 1 1 auto;
    display: flex;
    justify-content: center;
    flex-direction: column;
  } 

  :host {
    font-family: monospace;
    font-weight: bold;
  }
  #main-container {
    height: 27vh;
    width: 100vw; 
    border-top: 3px solid #ED6A5A;
    border-bottom: 3px solid #ED6A5A;
  }

  .row-container {
    height: 100%;
    display: flex;
    flex-directon: row;
    justify-content: flex-start;
    align-items: center;
  }
  
  information-table{
    height: 100%;
    width: 60%;
  }

  state-selection {
    height: 100%;
    width: 40%;
  }

  </style>
  <div id="main-container">
    <div class="row-container">
      <information-table></information-table>
      <state-selection 
        title = "State Selection"
        manualState = false 
        takerState = false
        makerState = false
        outState = true
        inventorySensitivyMin = 0
        inventorySensitivyMax = 10
        orderSensitivyMin = 0
        orderSensitivyMax = 10
        sliderStep = 0.1
      > </state-selection>
    </div>
  </div>


  <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
  `;
  
  }


}

window.customElements.define('interactive-component', InteractiveComponent);
