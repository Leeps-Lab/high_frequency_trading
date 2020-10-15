import {html,PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';

class EquationsTable extends PolymerElement {

    static get properties() {
        return {
            numPlayers: Number,
            inventory: Number,
            referencePrice: Number,
            initialEndowment: Number,
            totalBids: Number,
            totalAsks: Number,
            avgBidPrice: Number,
            avgAskPrice: Number,
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
                    <div>Gross Payoff </div>
                    <div>{{ _grossPayoff() }}</div>
                </div>
                <div class="col operator">
                    <div> - </div>
                    <div> - </div>
                </div>
                <div class="col">
                    <div>Tax Payment</div>
                    <div>{{ _taxPayment() }}</div>
                </div>
                <div class="col operator">
                    <div> - </div>
                    <div> - </div>
                </div>
                <div class="col">
                    <div>Speed Cost</div>
                    <div>{{ _speedCost() }}</div>
                </div>
            </div>
            <ul>
                <li>
                <div class="row">
                    <div class="col">
                        <div class="red">Gross Payoff</div>
                        <div>{{ _grossPayoff() }}</div>
                    </div>
                    <div class="col operator">
                        <div>= </div>
                        <div>= </div>
                    </div>
                    <div class="col">
                        <div>Final Cash</div>
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
                </div>
                <ul>
                    <li>
                    <div class="row">
                        <div class="col">
                            <div class="red">Final Cash</div>
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
                            <div>[[ totalAsks ]]</div>
                        </div>
                        <div class="col operator">
                            <div>&times;</div>
                            <div>&times;</div>
                        </div>
                        <div class="col">
                            <div>Avg. Sale Price</div>
                            <div>[[ _digitCorrector(avgAskPrice) ]]</div>
                        </div>
                        <div class="col operator">
                            <div>] - [</div>
                            <div>] - [</div>
                        </div>
                        <div class="col">
                            <div>Bought Units</div>
                            <div>[[ totalBids ]]</div>
                        </div>
                        <div class="col operator">
                            <div>&times;</div>
                            <div>&times;</div>
                        </div>
                        <div class="col">
                            <div>Avg. Buy Price</div>
                            <div>[[ _digitCorrector(avgBidPrice) ]]</div>
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
                            <div>[[ totalBids ]]</div>
                        </div>
                        <div class="col operator">
                            <div>-</div>
                            <div>-</div>
                        </div>
                        <div class="col">
                            <div>Units Sold</div>
                            <div>[[ totalAsks ]]</div>
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
                </ul>
                </li>
                
                <li>
                <div class="row">
                    <div class="col">
                        <div class="red">Tax Payment</div>
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
                        <div>Tax Rate</div>
                        <div>[[ taxRate ]]</div>
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
        </ul>
        `;
    }

    _round2Decimal(value) {
        return parseFloat((value).toFixed(2));
    }

    //Adjust number to the correct value by multiplying by .0001 
    _digitCorrector(value) {
        return this._round2Decimal(value * .0001);
    }

    _inventoryVal() {
        return this.inventory * this.referencePrice * .0001;
    }

    _finalCash() {
        return this._round2Decimal(this._digitCorrector(this.initialEndowment) + (this.totalAsks * this._digitCorrector(this.avgAskPrice)) - (this.totalBids * this._digitCorrector(this.avgBidPrice)));
    }

    _grossPayoff() {
        return this._round2Decimal(this._finalCash() + this._inventoryVal());
    }

    _taxPayment() {
        return this._round2Decimal(Math.abs(this._inventoryVal()) * this.taxRate);
    }

    _payoff() {
        return this._round2Decimal(this._grossPayoff() - this._taxPayment() - this._speedCost()); 
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
                return this._round2Decimal(speedCosts[player]);
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
}

window.customElements.define('equations-table', EquationsTable);