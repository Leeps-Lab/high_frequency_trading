import {html,PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';

class EquationsTable extends PolymerElement {

    static get properties() {
        return {
            numPlayers: Number,
            inventory: Number,
            referencePrice: Number,
            initialEndowment: Number,
            totalBids: Object,
            totalAsks: Object,
            sumBidPrice: Object,
            sumAskPrice: Object,
            taxRate: Number,
            subscriptionTime: Number,
            speedPrice: Number,
            speedCosts: Object,
            names: Object,
            nets: Object,
        };
    }

    static get template() {
        return html`
        
        <style>

            :host {
                display: block;
            }

            .row {
                display: flex;
                min-width: 0;
                padding: 3px;    
            }

            .col {
                display: flex;
                flex-direction: column;
                justify-content: center;
            }

            .col > div {
                margin: 1px;
                text-align: center;
            }

            .col > div:last-child {
                font-weight: bold;
            }

            .operator > div:last-child {
                font-weight: initial;
            }

            .red {
                color: red;
                font-weight: bold;
            }

            ul { 
                list-style: none; 
            }
           
        </style>

        <ul >
            <li>
            <div class="row">
                <div class="col">
                    <div class="red">Payoff</div>
                    <div>{{ _payoff() }}</div>
                </div>
                <div class="col operator">
                    <div>= </div>
                    <div>= </div>
                </div>
                <div class="col">
                    <div>PBD</div>
                    <div>{{ _grossPayoff() }}</div>
                </div>
                <div class="col operator">
                    <div> - </div>
                    <div> - </div>
                </div>
                <div class="col">
                    <div>Deduction</div>
                    <div>{{ _taxPayment() }}</div>
                </div>
            </div>
            <ul>
                <li>
                <div class="row">
                    <div class="col">
                        <div class="red">PBD</div>
                        <div>{{ _grossPayoff() }}</div>
                    </div>
                    <div class="col operator">
                        <div>= </div>
                        <div>= </div>
                    </div>
                    <div class="col">
                        <div>Cash</div>
                        <div>{{ _finalCash() }}</div>
                    </div>
                    <div class="col operator">
                        <div> + </div>
                        <div> + </div>
                    </div>
                    <div class="col">
                        <div>Inventory Value</div>
                        <div>{{ _inventoryVal() }}</div>
                    </div>
                    <div class="col operator">
                        <div> - </div>
                        <div> - </div>
                    </div>
                    <div class="col">
                        <div>Speed Cost</div>
                        <div>{{ _speedCostCalculation() }}</div>
                    </div>
                </div>
                <ul>
                    <li>
                    <div class="row">
                        <div class="col">
                            <div class="red">Cash</div>
                            <div>{{ _finalCash() }}</div>
                        </div>
                        <div class="col operator">
                            <div>=</div>
                            <div>=</div>
                        </div>
                        <div class="col">
                            <div>Init. Cash</div>
                            <div>[[ _digitCorrector(initialEndowment) ]]</div>
                        </div>
                        <div class="col operator">
                            <div>+ [</div>
                            <div>+ [</div>
                        </div>
                        <div class="col">
                            <div>Sold Units</div>
                            <div>[[ getTotalAsks() ]]</div>
                        </div>
                        <div class="col operator">
                            <div>&times;</div>
                            <div>&times;</div>
                        </div>
                        <div class="col">
                            <div>Avg. Sale Price</div>
                            <div>[[ getAvgAskPrice() ]]</div>
                        </div>
                        <div class="col operator">
                            <div>] - [</div>
                            <div>] - [</div>
                        </div>
                        <div class="col">
                            <div>Bought Units</div>
                            <div>[[ getTotalBids() ]]</div>
                        </div>
                        <div class="col operator">
                            <div>&times;</div>
                            <div>&times;</div>
                        </div>
                        <div class="col">
                            <div>Avg. Buy Price</div>
                            <div>[[ getAvgBidPrice() ]]</div>
                        </div>
                        <div class="col operator">
                            <div>]</div>
                            <div>]</div>
                        </div>
                    </div></li>

                    <li>
                    <div class="row">
                        <div class="col">
                            <div class="red">Inventory Value</div>
                            <div>[[ _inventoryVal() ]]</div>
                        </div>
                        <div class="col operator">
                            <div>= [</div>
                            <div>= [</div>
                        </div>
                        <div class="col">
                            <div>Units Purchased</div>
                            <div>[[ getTotalBids() ]]</div>
                        </div>
                        <div class="col operator">
                            <div>-</div>
                            <div>-</div>
                        </div>
                        <div class="col">
                            <div>Units Sold</div>
                            <div>[[ getTotalAsks() ]]</div>
                        </div>
                        <div class="col operator">
                            <div>] &times;</div>
                            <div>] &times;</div>
                        </div>
                        <div class="col">
                            <div>Ref. Price</div>
                            <div>[[ _digitCorrector(referencePrice) ]]</div>
                        </div>
                    </div>
                    </li>

                    <li> 
                    <div class="row">
                        <div class="col">
                            <div class="red">Speed Cost</div>
                            <div>{{ _speedCostCalculation() }}</div>
                        </div>
                        <div class="col operator">
                            <div>= </div>
                            <div>= </div>
                        </div>
                        <div class="col">
                            <div>Speed Price</div>
                            <div>{{ speedPrice }}</div>
                        </div>
                        <div class="col operator">
                            <div> &times; </div>
                            <div> &times; </div>
                        </div>
                        <div class="col">
                            <div>Seconds Used</div>
                            <div>{{ _secondsSpeedUsed() }}</div>
                        </div>
                    </div>
                    </li>
                </ul>
                </li>
                
                <li>
                <div class="row">
                    <div class="col">
                        <div class="red">Deduction</div>
                        <div>{{ _taxPayment() }}</div>
                    </div>
                    <div class="col operator">
                        <div>= </div>
                        <div>= </div>
                    </div>
                    <div class="col">
                        <div>| Inventory Value |</div>
                        <div>| {{ _inventoryVal() }} |</div>
                    </div>
                    <div class="col operator">
                        <div> &times; </div>
                        <div> &times; </div>
                    </div>
                    <div class="col">
                        <div>Deduction Rate</div>
                        <div>{{ _toPercentage(taxRate) }} %</div>
                    </div>
                </div>
                </li>

                
            </ul>
            </li>
        </ul>
        `;
    }

    _round2Decimal(value) {
        return parseFloat((value).toFixed(5));
    }

    //Adjust number to the correct value by multiplying by .0001 
    _digitCorrector(value) {
        return this._round2Decimal(value * .0001);
    }

    _inventoryVal() {
        return this.inventory * this.referencePrice * .0001;
    }

    _finalCash() {
        return this._round2Decimal(this._digitCorrector(this.initialEndowment) + (this.getTotalAsks() * this.getAvgAskPrice()) - (this.getTotalBids() * this.getAvgBidPrice()));
    }

    _grossPayoff() {
        return this._round2Decimal(this._finalCash() + this._inventoryVal() - this._speedCost());
    }

    _taxPayment() {
        return this._round2Decimal(Math.abs(this._inventoryVal()) * this.taxRate);
    }

    _toPercentage(value) {
        return value * 100
    }

    _payoff() {
        return parseFloat((this._grossPayoff() - this._taxPayment()).toFixed(2)); 
    }

    _speedCost() {
        // initialize arrays for Polymer arguments
        let payoffs = this.nets;
        this.numPlayers = Object.keys(payoffs).length;
        const speedCosts = this.speedCosts;
        const names = this.names;
        let player = 0;

        for(let i = 0; i < this.numPlayers; i++) {
            player = Object.keys(payoffs)[i];
            
            if(names[player] == 'You') {
                return parseFloat((speedCosts[player]).toFixed(2));
            }
        } 
    }

    _secondsSpeedUsed() {
        return Math.round(this._speedCost() / this.speedPrice);
    }

    _speedCostCalculation() {
        //return this.speedPrice * this.subscriptionTime;
        return this._round2Decimal(this.speedPrice * this._secondsSpeedUsed());
    }

    getTotalBids() {
        let payoffs = this.nets;
        this.numPlayers = Object.keys(payoffs).length;
        const totalBids = this.totalBids;
        const names = this.names;
        let player = 0;

        for(let i = 0; i < this.numPlayers; i++) {
            player = Object.keys(payoffs)[i];
            
            if(names[player] == 'You') {
                return totalBids[player];
            }
        } 
    }

    getTotalAsks() {
        let payoffs = this.nets;
        this.numPlayers = Object.keys(payoffs).length;
        const totalAsks = this.totalAsks;
        const names = this.names;
        let player = 0;

        for(let i = 0; i < this.numPlayers; i++) {
            player = Object.keys(payoffs)[i];
            
            if(names[player] == 'You') {
                return totalAsks[player];
            }
        } 
    }

    getAvgBidPrice() {
        let payoffs = this.nets;
        this.numPlayers = Object.keys(payoffs).length;
        const sumBidPrice = this.sumBidPrice;
        const names = this.names;
        let player = 0;

        for(let i = 0; i < this.numPlayers; i++) {
            player = Object.keys(payoffs)[i];
            
            if(names[player] == 'You') {
                if (this.getTotalBids() == 0) {
                    return 0;
                } else {
                    return this._digitCorrector(sumBidPrice[player] / this.getTotalBids());
                }   
            }
        } 
    }

    getAvgAskPrice() {
        let payoffs = this.nets;
        this.numPlayers = Object.keys(payoffs).length;
        const sumAskPrice = this.sumAskPrice;
        const names = this.names;
        let player = 0;

        for(let i = 0; i < this.numPlayers; i++) {
            player = Object.keys(payoffs)[i];
            
            if(names[player] == 'You') {
                if (this.getTotalAsks() == 0) {
                    return 0;
                } else {
                    return this._digitCorrector(sumAskPrice[player] / this.getTotalAsks());
                }
            }
        } 
    }
}

window.customElements.define('equations-table', EquationsTable);