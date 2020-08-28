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
      .child {
        border: 1px solid black;
        text-align: center;
      }


      #myPayoffs, th, td {
        border: 1px solid black;
        
      }

      equations-table {
        width: 50%;
        margin: auto;
      }

    </style>

    <h1 style="text-align:center; margin-bottom: 30px;">Trade Session Results</h1>
    <hr style="width: 60%">

    <h3 style="text-align:center; margin-bottom: 20px;">Your Payoff Calculations</h3>

    <equations-table
      inventory="[[inventory]]"
      reference-price="[[referencePrice]]"
      initial-endowment="[[initialEndowment]]"
      total-bids="[[totalBids]]"
      total-asks="[[totalAsks]]"
      avg-bid-price="[[avgBidPrice]]"
      avg-ask-price="[[avgAskPrice]]"
      tax-rate="[[taxRate]]"
      subscription-time="[[subscriptionTime]]"
      speed-price="[[speedPrice]]"
      speed-costs="{{speedCosts}}"
      names="{{names}}"
      nets="{{nets}}"
    ></equations-table>

    <!-- <table id="myPayoffs" style="width:55%; text-align: center; margin-left: auto; margin-right: auto;"> 
      <tr>
        <th> Variables </th>
        <th> Equations </th>
        <th> Results </th>
      </tr>

      <tr>
        <td>Final Cash </td>
        <td>Initial Cash + [#unitsSold x avgSalesPrice] - [#unitsPurchased x avgPurchasePrice]</td>
        <td>[[ _digitCorrector(initialEndowment) ]] +  [[[ totalAsks ]] x [[ _digitCorrector(avgAskPrice) ]]]  -  [[[ totalBids ]] x [[ _digitCorrector(avgBidPrice) ]]] = {{ _finalCash() }}</td>
      </tr>

      <tr>
        <td>Inventory Size</td>
        <td>#unitsPurchased - #unitsSold</td>
        <td>[[ totalBids ]] - [[ totalAsks ]] = [[ inventory ]]</td>
      </tr>

      <tr>
        <td>Inventory Value</td>
        <td>Inventory Size x Reference Price</td>
        <td>[[ inventory ]] x [[ _digitCorrector(referencePrice) ]] = {{ _inventoryVal() }}</td>
      </tr>

      <tr>
        <td>Final Wealth</td>
        <td>Final Cash + Inventory Value</td>
        <td>{{ _finalCash() }} + {{ _inventoryVal() }} = {{ _finalWealth() }}</td>
      </tr>

      <tr>
        <td>Tax Payment</td>
        <td>| Inventory Value | x taxRate</td>
        <td>| {{ _inventoryVal() }} | x [[ taxRate ]] = {{ _taxPayment() }}</td>
      </tr>

      <tr>
        <td>Speed Cost</td>
        <td>Speed Price x Seconds Used</td>
        <td>{{ speedPrice }} x {{ _secondsSpeedUsed() }} = {{ _speedCostCalculation() }}</td>
      </tr>

      <tr>
        <td>Net Payoff</td>
        <td>Final Wealth - Tax Payment - Speed Cost</td>
        <td>{{ _finalWealth() }} - {{ _taxPayment() }} - {{ _speedCost() }} = {{ _payoff() }}</td>
      </tr>

    
    

    </table> -->

    <div id="outer" class="parent" style="text-align:center;">
    </div>
    `;
  }

  connectedCallback() {
    super.connectedCallback();
    //let payoffs = this.payoffs;

    // initialize arrays for Polymer arguments
    let payoffs = this.nets;
    this.numPlayers = Object.keys(payoffs).length;
    const strategies = this.strategies;
    const invs = this.invSensitivities;
    const sigs = this.signedVolumes;
    const feeds = this.externalFeeds;
    const names = this.names;
    const taxes = this.taxes;
    const speedCosts = this.speedCosts;

    // set number of rows equal to the closest perfect square
    const numRows = Math.round(Math.sqrt(this.numPlayers));
    const cellsPerRow = Math.round((this.numPlayers)/numRows);

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
    const height = (window.innerHeight * 0.85)/numRows;

    let charts = document.createElement("table");

    charts.setAttribute("style", "width:100%; border-collapse:separate; border-spacing: 0 50px; ");
    let rows = []
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

    let currCell = 0;
    let cellCount = 0;

    //Loops through each player's results and creates its own individual results-cell 
    for(let i = 0; i < this.numPlayers; i++) {
      let high = Object.keys(payoffs)[0];

      //Put your payoff cell at the front
      if(i == 0) {
        high = player;
      }
      else {
        //Find player with highest payoff that's left in the payoffs list
        for(let key in payoffs) {
          if(payoffs[key] > payoffs[high]) {
            high = key;
          }
        }
      }

      let myNet = payoffs[high];
      let myTax = taxes[high];
      let mySpeedCost = speedCosts[high];
      let myName = names[high];
      let myStrategies = strategies[high];
      let myInv = invs[high];
      let mySig = sigs[high];
      let myFeed = feeds[high];

      //let cell = document.createElement("td");
      //cell.setAttribute("style", "display:inline-block");
      let node = document.createElement("div");
      node.setAttribute("class", "child");
      let child = document.createElement("results-cell");
      //console.log('mipayoff', myPayoff)
      child.net = myNet;
      child.tax = myTax;
      child.speedCost = mySpeedCost;
      child.name = myName;
      child.strategies = myStrategies;
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
        type: Number,
      },
      totalAsks: {
        type: Number,
      },
      avgBidPrice: {
        type: Number,
      },
      avgAskPrice: {
        type: Number,
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
      }
    }
  }

}

window.customElements.define('results-page', ResultsPage);
