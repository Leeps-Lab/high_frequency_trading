import {html, PolymerElement}  from '../node_modules/@polymer/polymer/polymer-element.js';

class ProfitGraph extends PolymerElement {

    static get template() {
        return html`
            <style>
                :host {
                    display: block;
                }
            </style>
            <div id='chart'></div>
        `;
    }

    static get properties() {
        return {
            profit: {
                type: Number,
                observer: '_addPayoff',
            },
            _xRange: {
                type: Number,
                value: 10000,
            }
        };
    }

    connectedCallback() {
        super.connectedCallback();

        this.width = this.offsetWidth;
        this.height = this.offsetHeight;

        this._initHighchart();
    }

    start() {
        this.startTime = performance.now();
        console.log(this.startTime)
        this.chart.get('xAxis').update({
            visible: true,
            min: this.startTime,
            max: this.startTime + this._xRange,
        });

        if (this.payoff) {
            this._addPayoff(this.payoff);
        }
    }

    _addPayoff(payoff) {
        if (!this.startTime) return;

        const profitSeries = this.chart.get('profit');
        const numPoints = profitSeries.data.length;
        if (numPoints) {
            profitSeries.data[numPoints - 1].remove(false);
        }
        const now = performance.now();
        profitSeries.addPoint([
            now, payoff
        ], false);
        profitSeries.addPoint([
            now, payoff
        ], false);
        this.chart.redraw();
        console.log(profitSeries.data)
    }

    _initHighchart() {
        const self = this;

        this.chart = Highcharts.chart({
            chart: {
                animation: false,
                renderTo: this.$.chart,
                width: this.width,
                height: this.height,
            },
            title: { 
                text: null
            },
            exporting: { enabled: false },
            tooltip: { enabled: false },
            legend: { enabled: false },
            credits: { enabled: false },
            xAxis: {
                id: 'xAxis',
                visible: false,
                type: 'datetime',
                labels: {
                    formatter: function() {
                        return Highcharts.dateFormat('%M:%S', this.value - self.startTime);
                    },
                },
            },
            yAxis: {
                title: { text: 'Profit'},
                labels: { enabled: true },
            },
            plotOptions: {
                series: {
                    animation: false,
                    dataLabels: { enabled: false },
                    states: { hover: { enabled: false } },
                },
                line: {
                    step: 'left',
                    marker: { enabled: false },
                },
            },
            series: [
                {
                    id: 'profit',
                    type: 'line',
                },
            ],
        });
    }

}


window.customElements.define('profit-graph', ProfitGraph);
