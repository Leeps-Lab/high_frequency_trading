import {html,PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';

import "./results-cell.js";

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

      .outer {
        display: flex;
        justify-content: space-around;
        padding: 5px;
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
    
    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">

    <style>
      .child {
        border: 1px solid black;
        text-align: center;
      }

      #myPayoffs, th, td {
        border: 1px solid black;
      }

    </style>

    <h1 style="text-align:center; margin-bottom: 30px;">Trade Session Results</h1>
    <hr style="width: 60%">

    <h3 style="text-align:center; margin-bottom: 20px;">Your Payoff Calculations</h3>

    <table id="myPayoffs" style="width:55%; text-align: center; margin-left: auto; margin-right: auto;"> 
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
        <td>Tax Payment</td>
        <td>| Inventory Value | x taxRate</td>
        <td>| {{ _inventoryVal() }} | x [[ taxRate ]] = {{ _taxPayment() }}</td>
      </tr>

      <tr>
        <td>Final Wealth</td>
        <td>Final Cash + Inventory Value</td>
        <td>{{ _finalCash() }} + {{ _inventoryVal() }} = {{ _finalWealth() }}</td>
      </tr>

      <tr>
        <td>Payoff</td>
        <td>Final Wealth - Tax Payment - Speed Cost</td>
        <td>{{ _finalWealth() }} - {{ _taxPayment() }} - {{ _speedCost() }} = {{ _payoff() }}</td>
      </tr>

    
    <!--
      <tr style="border: 1px solid black;">
        <td style="border: 1px solid black;">
          <b>Final Cash = Initial Cash + [#unitsSold x avgSalesPrice] - [#unitsPurchased x avgPurchasePrice]</b>
          <p>Final Cash = [[ _digitCorrector(initialEndowment) ]] +  [[[ totalAsks ]] x [[ _digitCorrector(avgAskPrice) ]]]  -  [[[ totalBids ]] x [[ _digitCorrector(avgBidPrice) ]]] = {{ _finalCash() }}</p>
        </td>

        <td style="border: 1px solid black;">
          <b>Tax Payment = | Inventory Value | x taxRate</b>
          <p>Tax Payment = | {{ _inventoryVal() }} | x [[ taxRate ]] = {{ _taxPayment() }}</p>
        </td>
      </tr>

      <tr style="border: 1px solid black;">
        <td style="border: 1px solid black;">
          <b>Inventory Size = #unitsPurchased - #unitsSold</b>
          <p>Inventory Size = [[ totalBids ]] - [[ totalAsks ]] = [[ inventory ]]</p>
        </td>

        <td style="border: 1px solid black;">
          <b>Final Wealth = Final Cash + Inventory Value</b>
          <p>Final Wealth = {{ _finalCash() }} + {{ _inventoryVal() }} = {{ _finalWealth() }}</p>
        </td>
      </tr>

      <tr style="border: 1px solid black;">
        <td style="border: 1px solid black;">  
          <b>Inventory Value = Inventory Size x Reference Price</b>
          <p>Inventory Value = [[ inventory ]] x [[ _digitCorrector(referencePrice) ]] = {{ _inventoryVal() }}</p>
        </td>

        <td style="border: 1px solid black;">
            <b>Payoff = Final Wealth - Tax Payment - Speed Cost</b>
            <p>Payoff = {{ _finalWealth() }} - {{ _taxPayment() }} - {{ _speedCost() }} = {{ _payoff() }}</p> 
        </td>
      </tr>
    -->

    </table>

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
    const cellsPerRow = Math.round(this.numPlayers/numRows);

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

    let currCell = 0;
    let cellCount = 0;

    //Loops through each player's results and creates its own individual results-cell 
    for(let i = 0; i < this.numPlayers; i++) {
      let low = Object.keys(payoffs)[0];

      //Find lowest payoff
      for(let key in payoffs) {
        if(payoffs[key] > payoffs[low]) {
          low = key;
        }
      }

      let myNet = payoffs[low];
      let myTax = taxes[low];
      let mySpeedCost = speedCosts[low];
      let myName = names[low];
      let myStrategies = strategies[low];
      let myInv = invs[low];
      let mySig = sigs[low];
      let myFeed = feeds[low];

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

      delete payoffs[low];
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
    }
  }


  //Adjust number to the correct value by multiplying by .0001 and rounding
  _digitCorrector(value) {
    return value * .0001;
  }

  _inventoryVal() {
    return this.inventory * this.referencePrice * .0001;
  }

  _finalCash() {
    return this._digitCorrector(this.initialEndowment) + (this.totalAsks * this._digitCorrector(this.avgAskPrice)) - (this.totalBids * this._digitCorrector(this.avgBidPrice));
  }

  _finalWealth() {
    return this._finalCash() + this._inventoryVal();
  }

  _taxPayment() {
    return Math.abs(this._inventoryVal()) * this.taxRate;
  }

  _payoff() {
    return (this._finalWealth() - this._taxPayment() - this._speedCost()).toFixed(2); 
  }

  _speedCost() {
    // initialize arrays for Polymer arguments
    let payoffs = this.nets;
    this.numPlayers = Object.keys(payoffs).length;
    const speedCosts = this.speedCosts;

    let low = 0;

    for(let i = 0; i < this.numPlayers; i++) {
      low = Object.keys(payoffs)[0];
      for(let key in payoffs) {
        if(payoffs[key] > payoffs[low]) {
          low = key;
        }
      }
    }
    return speedCosts[low];
  }
}

window.customElements.define('results-page', ResultsPage);
