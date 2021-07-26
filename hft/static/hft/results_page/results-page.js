import {html,PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';

import "./results-cell.js";
import "./equations-table.js";


/*
 * This will hopefully be the component used for the results page at some point.
 *
 * Pie chart cannibalized from https://www.highcharts.com/demo/pie-legend
 */
class ResultsPage extends PolymerElement {
  constructor(){
    super();
  }

  static get template() {
    return html `

    <style>
      * {
        box-sizing: border-box;
      }
      .child {
        border: 1px solid black;
        text-align: center;
        display: inline-block;
        overflow: auto;
        white-space: nowrap;
      }

      #myPayoffs, th, td {
        border: 1px solid black;
      }

      equations-table {
        height: 90%;
        width: 100%;
      }

    </style>

    <h1 style="text-align:center; margin-bottom: 30px;">Trade Session Results</h1>

    <table id = "myPayoff" style="width:100%; border-collapse:separate; border-spacing: 0 50px;">

      <div style="display:flex; justify-content:space-around;">
        <div id = "myResultsCell">
        </div>

        <div id="equationsTable" class="child">
          <h3 style="text-align:center; margin-top:10px; margin-bottom: 0px;">Your Payoff Calculations</h3>
          <equations-table
            inventory="[[inventory]]"
            reference-price="[[referencePrice]]"
            initial-endowment="[[initialEndowment]]"
            total-bids="{{totalBids}}"
            total-asks="{{totalAsks}}"
            sum-bid-price="{{sumBidPrice}}"
            sum-ask-price="{{sumAskPrice}}"
            tax-rate="[[taxRate]]"
            speed-price="[[speedPrice]]"
            speed-costs="{{speedCosts}}"
            names="{{names}}"
            nets="{{nets}}"
          ></equations-table>
        </div>
      </div>
    </table>

    <div id="outer" class="parent" style="text-align:center;"></div>
    `;
  }

  connectedCallback() {
    super.connectedCallback();
    //let payoffs = this.payoffs;

    // initialize arrays for Polymer arguments
    let payoffs = this.nets;
    this.numPlayers = Object.keys(payoffs).length;
    const strategies = this.strategies;
    const speedUsage = this.speedUsage;
    const invs = this.invSensitivities;
    const sigs = this.signedVolumes;
    const feeds = this.externalFeeds;
    const names = this.names;
    const taxes = this.taxes;
    const speedCosts = this.speedCosts;

    // set number of rows equal to the closest perfect square
    const numRows = Math.round(Math.sqrt(this.numPlayers)) + 1;
    //const cellsPerRow = Math.round((this.numPlayers)/numRows);
    const cellsPerRow = 2;

    // set dimensions for cells
    let widthScale = cellsPerRow;
    /*
    if(cellsPerRow <= this.numPlayers/numRows) {
      widthScale = cellsPerRow;
    }
    else {
      widthScale = cellsPerRow + this.numPlayers % numRows;
    } */
    const width = (window.innerWidth * 0.85)/widthScale;
    const height = (window.innerHeight * 0.85)/Math.round(Math.sqrt(this.numPlayers));

    //Set width and height of equations table
    var equationsTable = this.shadowRoot.getElementById("equationsTable");
    equationsTable.style.width = width + "px";
    equationsTable.style.height = (height + 17.5) + "px";

    //Ensures equation table's width and  height doesn't adjust when the window is resized
    equationsTable.style.minWidth = width + "px";
    equationsTable.style.minHeight = (height + 17.5) + "px";

    let charts = document.createElement("table");

    charts.setAttribute("style", "width:100%; border-collapse:separate; border-spacing: 0 50px; ");
    let rows = [];
    for(let i = 0; i < numRows; i++) {
      let row = document.createElement("div");
      row.setAttribute("style", "display:flex; justify-content:space-around;");
      rows.push(row);
    }

    //Find my player ID
    let player = 0;
    for(let i = 0; i < this.numPlayers; i++) {
      player = Object.keys(payoffs)[i];
      if(names[player] == 'You') {
        break;
      }
    }

    //Grab my payoff cell
    let myNet = payoffs[player];
    let myTax = taxes[player];
    let mySpeedCost = speedCosts[player];
    let myName = names[player];
    let myStrategies = strategies[player];
    let mySpeedUsage = speedUsage[player];
    
    let myInv = invs[player];
    let mySig = sigs[player];
    let myFeed = feeds[player];

    let node = document.createElement("div");
    node.setAttribute("class", "child");
    let child = document.createElement("results-cell");
    child.net = myNet;
    child.tax = myTax;
    child.subscriptionTime = this.subscriptionTime
    child.speedCost = mySpeedCost;
    child.name = myName;
    child.strategies = myStrategies;
    child.speedUsage = mySpeedUsage;
    child.invSensitivity = myInv;
    child.signedVolume = mySig;
    child.externalFeed = myFeed;
    child.width = width;
    child.height = height;
    node.width = width;
    node.height = height;
    node.appendChild(child);
    this.$.myResultsCell.appendChild(node); 
    delete payoffs[player];
    
    let currCell = 0;
    let cellCount = 0;

    //Loops through each player's results and creates its own individual results-cell 
    for(let i = 0; i < this.numPlayers - 1; i++) {
      let high = Object.keys(payoffs)[0];

      //Find player with highest payoff that's left in the payoffs list
      for(let key in payoffs) {
        if(payoffs[key] > payoffs[high]) {
          high = key;
        }
      }

      myNet = payoffs[high];
      myTax = taxes[high];
      mySpeedCost = speedCosts[high];
      myName = names[high];
      myStrategies = strategies[high];
      mySpeedUsage = speedUsage[high];
      myInv = invs[high];
      mySig = sigs[high];
      myFeed = feeds[high];

      //let cell = document.createElement("td");
      //cell.setAttribute("style", "display:inline-block");
      node = document.createElement("div");
      node.setAttribute("class", "child");
      child = document.createElement("results-cell");
      //console.log('mipayoff', myPayoff)
      child.net = myNet;
      child.tax = myTax;
      child.speedCost = mySpeedCost;
      child.name = myName;
      child.strategies = myStrategies;
      child.speedUsage = mySpeedUsage;
      child.invSensitivity = myInv;
      child.signedVolume = mySig;
      child.externalFeed = myFeed;
      child.width = width;
      child.height = height;
      node.width = width;
      node.height = height;
      node.appendChild(child);
      //cell.appendChild(node);
      //const pos = Math.ceil(i/numRows - 1);
      //console.log(pos);
      //rows[currCell].appendChild(cell);
      rows[currCell].appendChild(node);

      cellCount++;
      if(cellCount >= cellsPerRow && currCell != numRows) {
        currCell++;
        cellCount = 0;
      }
      //this.$.outer.appendChild(node);

      delete payoffs[high];
    }

    for(let i = 0; i < rows.length; i++) {
      let bigRow = document.createElement("tr");
      bigRow.appendChild(rows[i]);
      //charts.appendChild(rows[i]);
      charts.appendChild(bigRow);
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
        //value: {player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40}
      },
      taxes: {
        type: Object,
        //value: {player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40}
      },
      speedCosts: {
        type: Object,
      },
      names: {
        type: Object,
        //value: {player:"Player",foo:"Trader 1",bar:"Trader 2",the:"Trader 3",a:"a",b:"b",c:"c",d:"d"}
      },
      strategies: {
        type: Object,
        //value: {player:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},foo:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},bar:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},the:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},a:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},b:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},c:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},d:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40}}
      },
      speedUsage: {
        type: Object,
        //value: {player:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},foo:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},bar:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},the:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},a:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},b:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},c:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40},d:{player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40}}
      },
      invSensitivities: {
        type: Object,
        //value: {player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40}
      },
      signedVolumes: {
        type: Object,
        //value: {player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40}
      },
      externalFeeds: {
        type: Object,
        //value: {player:30,foo:20,bar:90,the:40,a:30,b:20,c:90,d:40}
      },
      inventory: {
        type: Number,
      },
      referencePrice: {
        type: Number,
      },
      initialEndowment: {
        type: Number,
      },
      totalBids: {
        type: Object,
      },
      totalAsks: {
        type: Object,
      },
      sumBidPrice: {
        type: Object,
      },
      sumAskPrice: {
        type: Object,
      },
      taxRate: {
        type: Number,
      },
      subscriptionTime: {
        type: Number,
      },
      speedPrice: {
        type: Number,
        value: () => {
          return parseFloat((OTREE_CONSTANTS.speedCost * .0001).toFixed(3));
        }
      },
      width: {
        type: Number
      },
      height: {
        type: Number
      }
    }
  }


}

window.customElements.define('results-page', ResultsPage);
