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
  spread-graph{
    width:100%;
  }

  info-table{
    float:left;
    width: 40%;
  }
  </style>
  <spread-graph></spread-graph>
  <div style="border:solid 1px rgb(200,200,200); height: 108px;">
    <info-table></info-table>
    <input-section></input-section>
  </div>


  <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
  `;
  }


}

window.customElements.define('interactive-component', InteractiveComponent);
