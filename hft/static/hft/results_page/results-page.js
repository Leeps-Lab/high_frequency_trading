import {html,PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';
import "./results-cell.js";

/*
 * This will hopefully be the component used for the results page at some point.
 */
class ResultsPage extends PolymerElement {
  constructor(){
    super();
  }

  static get template() {
    return html `
    <!--
    <style>

      .parent {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-items: flex-start;
        align-content: space-around;
        height: 0px;
      }

      .child {
        display: flex;
        flex: 1;
        flex-basis: 50%;
        overflow: hidden;
        border: 1px solid black;
        width: 100px;
        height: 500px;
      }

    </style> -->

    <style>
      .child {
        border: 1px solid black;
        text-align: center;
      }

    </style>

    <div id="outer" class="parent" style="text-align:center">
    </div>
    `;
  }

  connectedCallback() {
    super.connectedCallback();
    //let payoffs = this.payoffs;

    // initialize arrays for Polymer arguments
    let payoffs = this.nets;
    this.numPlayers = Object.keys(payoffs).length
    const strategies = this.strategies;
    const invs = this.invSensitivities;
    const imbs = this.imbSensitivities;
    const names = this.names;
    const taxes = this.taxes;

    // set number of rows equal to the closest perfect square
    const numRows = Math.round(Math.sqrt(this.numPlayers));
    const cellsPerRow = Math.round(this.numPlayers/numRows);

    // set dimensions for cells
    let widthScale;
    if(cellsPerRow <= this.numPlayers/numRows) {
      widthScale = cellsPerRow;
    }
    else {
      widthScale = cellsPerRow + this.numPlayers % numRows;
    }
    const width = (window.innerWidth * 0.85)/widthScale;
    const height = (window.innerHeight * 0.85)/numRows;

    let charts = document.createElement("table");
    charts.setAttribute("style", "display:inline-block");
    let rows = []

    // create rows
    for(let i = 0; i < numRows; i++) {
      let row = document.createElement("tr");
      rows.push(row);
    }

    let currCell = 0;
    let cellCount = 0;

    // iterate through dictionaries by net payoff order
    for(let i = 0; i < this.numPlayers; i++) {
      let low = Object.keys(payoffs)[0];
      for(let key in payoffs) {
        if(payoffs[key] > payoffs[low]) {
          low = key;
        }
      }

      // create cell
      let myNet = payoffs[low];
      let myTax = taxes[low];
      let myName = names[low];
      let myStrategies = strategies[low];
      let myInv = invs[low];
      let myImb = imbs[low];

      let cell = document.createElement("td");
      cell.setAttribute("style", "display:inline-block");
      let node = document.createElement("div");
      node.setAttribute("class", "child");
      let child = document.createElement("results-cell");
      //console.log('mipayoff', myPayoff)
      child.net = myNet;
      child.tax = myTax;
      child.name = myName;
      child.strategies = myStrategies;
      child.invSensitivity = myInv;
      child.imbSensitivity = myImb;
      child.width = width;
      child.height = height;
      node.appendChild(child);
      cell.appendChild(node);
      //const pos = Math.ceil(i/numRows - 1);
      //console.log(pos);
      rows[currCell].appendChild(cell);
      cellCount++;
      if(cellCount >= cellsPerRow && currCell != numRows) {
        currCell++;
        cellCount = 0;
      }
      //this.$.outer.appendChild(node);

      delete payoffs[low];
    }

    for(let i = 0; i < rows.length; i++) {
      charts.appendChild(rows[i]);
    }
    this.$.outer.appendChild(charts);
  }


  static get properties() {
    return {
      numPlayers: {
        type: Number,
      },
      /*
      payoffs: {
        type: Object,
        //value: {player:30,foo:20,bar:90,the:40}
      },*/
      nets: {
        type: Object,
        //value: {player:30,foo:20,bar:90,the:40}
      },
      taxes: {
        type: Object,
        //value: {player:10,foo:15,bar:13,the:20}
      },
      names: {
        type: Object,
        //value: {player:"Player",foo:"Trader 1",bar:"Trader 2",the:"Trader 3"}
      },
      strategies: {
        type: Object,
        //value: {player:{player:30,foo:20,bar:90,the:40},foo:{player:30,foo:20,bar:90,the:40},bar:{player:30,foo:20,bar:90,the:40},the:{player:30,foo:20,bar:90,the:40}}
      },
      invSensitivities: {
        type: Object,
        //value: {player:40,foo:10,bar:90,the:30}
      },
      imbSensitivities: {
        type: Object,
        //value: {player:30,foo:20,bar:100,the:40}
      }
    }
  }

}

window.customElements.define('results-page', ResultsPage);
