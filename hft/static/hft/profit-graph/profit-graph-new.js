import {html, PolymerElement}  from '../node_modules/@polymer/polymer/polymer-element.js';

class ProfitGraph extends PolymerElement {

    static get template() {
        return html`
            <style>
                :host {
                    display: block;
                }

                .profit-line {
                    stroke: black;
                    stroke-width: 3;
                }
            </style>
            
            <svg id="svg"></svg>
        `;
    }

    static get properties() {
        return {
            profit: {
                type: Number,
                observer: '_addPayoff',
            },
            margin: {
                type: Object,
                value: {top: 40, left: 40, right: 10, bottom: 40},
            },
            xRange: {
                type: Number,
                value: 20000,
            },
            yRange: {
                type: Number,
                value: 10,
            },
            defaultYCenter: {
                type: Number,
                value: 100,
            },
            animationTime: {
                type: Number,
                value: 2000,
            },
            _profitHistory: {
                type: Array,
                value: () => [],
            },
        };
    }

    static get observers() {
        return [
            '_updateProfitLine(_profitHistory.splices)',
        ]
    }

    connectedCallback() {
        super.connectedCallback();

        this.width = this.offsetWidth - this.margin.left - this.margin.right;
        this.height = this.offsetHeight - this.margin.top - this.margin.bottom;

        this.init();
    }

    init() {
        this.mainGroup = d3.select(this.$.svg)
            .attr('width', this.offsetWidth)
            .attr('height', this.offsetHeight)
          .append('g')
            .attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');
        
        this.profitLines = this.mainGroup.append('g');

        this.xScale = d3.scaleTime()
            .domain([0, this.xRange])
            .range([0, this.width]);
        
        this.xAxis = d3.axisBottom()
            .scale(this.xScale);

        this.domXAxis = this.mainGroup.append("g")
            .attr("class", "axis axis-x")
            .attr("transform", "translate(0," + this.height + ")")
            .call(this.xAxis);

        this.yScale = d3.scaleLinear()
            .domain([
                this.defaultYCenter - this.yRange/2,
                this.defaultYCenter + this.yRange/2
            ])
            .range([this.height, 0]);
        
        this.yAxis = d3.axisLeft()
            .scale(this.yScale);

        this.domYAxis = this.mainGroup.append("g")
            .attr("class", "axis axis-y")
            .call(this.yAxis);
    }

    start() {
        const self = this;

        this.startTime = performance.now();

        this.xScale.domain([this.startTime, this.startTime + this.xRange]);

        const xTickFormat = d3.timeFormat('%M:%S');
        this.xAxis.scale(this.xScale)
            .tickFormat(d => xTickFormat(d - self.startTime));
        this.domXAxis.call(this.xAxis);

        if (this.payoff) {
            this._addPayoff(this.payoff);
        }

        window.requestAnimationFrame(this._tick.bind(this));
    }

    _tick() {
        const now = performance.now();

        if (now > this.startTime + this.xRange) {
            this.xScale.domain([now - this.xRange, now]);
            this.xAxis.scale(this.xScale);
            this.domXAxis.call(this.xAxis);
            this._updateProfitLine();
        }

        if (this.profit) {
            if (!this.currentProfitLine) {
                this.currentProfitLine = this.profitLines.append('line')
                    .attr('class', 'profit-line');
            }

            this.currentProfitLine
                .attr('x1', this.xScale(this._lastPayoffChangeTime))
                .attr('x2', this.xScale(now))
                .attr('y1', this.yScale(this.profit))
                .attr('y2', this.yScale(this.profit))
        }

        window.requestAnimationFrame(this._tick.bind(this));
    }

    _addPayoff(_newPayoff, oldPayoff) {
        const oldTime = this._lastPayoffChangeTime;
        this._lastPayoffChangeTime = performance.now();
        if (this._lastPayoffChangeTime) {
            this.push('_profitHistory', {payoff: oldPayoff, time: oldTime});
        }

        this._updateYScale();
        this._updateProfitLine();
    }

    _updateProfitLine() {
        if (!this.mainGroup || !this.startTime) {
            return;
        }

        const self = this;
        const profitHistory = this.get('_profitHistory');

        const lines = this.profitLines.selectAll('line')
            .data(profitHistory);

        lines.enter()
            .append('line')
            .attr('class', 'profit-line')
            .attr('x1', d =>  self.xScale(d.time))
            .attr('x2', (_, i) => self.xScale(i == profitHistory.length-1 ? self._lastPayoffChangeTime : profitHistory[i+1].time))
            .attr('y1', d => self.yScale(d.payoff))
            .attr('y2', d => self.yScale(d.payoff));
        
        lines
            .attr('x1', d =>  self.xScale(d.time))
            .attr('x2', (_, i) => self.xScale(i == profitHistory.length-1 ? self._lastPayoffChangeTime : profitHistory[i+1].time));
    }

    _updateYScale() {
        const yDomain = this.yScale.domain();
        const yRange = yDomain[1] - yDomain[0];
        if (this.profit > yDomain[0] + yRange/4 && this.profit < yDomain[1] - yRange/4) {
            return;
        }
        this.yScale.domain([
            this.profit - yRange/2,
            this.profit + yRange/2
        ]);
        this.yAxis.scale(this.yScale);
        this.domYAxis.transition()
            .duration(this.animationTime)
            .call(this.yAxis);
    }

}


window.customElements.define('profit-graph', ProfitGraph);
