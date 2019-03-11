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
            animationTime: {
                type: Number,
                value: 400,
            },
            _profitHistory: {
                type: Array,
                value: () => [],
            },
            _defaultYRange: {
                type: Array,
                value: [9800, 10200],
            },
            isRunning: {
                type: Boolean,
                value: false,
                observer: '_runningChanged'
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
        
        this.mainGroup.append('clipPath')
            .attr('id', 'lines-clip')
          .append('rect')
            .attr('width', this.width)
            .attr('height', this.height);
        
        this.profitLines = this.mainGroup.append('g');

        this.currentProfitLine = this.mainGroup.append('line')
            .attr('clip-path', 'url(#lines-clip)')
            .attr('class', 'profit-line');

        this.xScale = d3.scaleTime()
            .domain([0, this.xRange])
            .range([0, this.width]);
        
        this.xAxis = d3.axisBottom()
            .tickFormat(d3.timeFormat('%M:%S'))
            .scale(this.xScale);

        this.domXAxis = this.mainGroup.append("g")
            .attr("class", "axis axis-x")
            .attr("transform", "translate(0," + this.height + ")")
            .call(this.xAxis);

        this.yScale = d3.scaleLinear()
            .domain(this._defaultYRange)
            .range([this.height, 0]);
        
        this.yAxis = d3.axisLeft()
            .scale(this.yScale);

        this.domYAxis = this.mainGroup.append("g")
            .attr("class", "axis axis-y")
            .call(this.yAxis);
    }

    _runningChanged(isRunning) {
        if (isRunning) {
            this.start()
        }
    }

    start() {
        this.startTime = performance.now();

        this.xScale.domain([this.startTime, this.startTime + this.xRange]);
        this.xAxis.scale(this.xScale);
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

        this.currentProfitLine
            .attr('x1', this.xScale(this._lastPayoffChangeTime))
            .attr('x2', this.xScale(now));

        window.requestAnimationFrame(this._tick.bind(this));
    }

    _addPayoff(newProfit, oldProfit) {
        const oldTime = this._lastPayoffChangeTime;
        this._lastPayoffChangeTime = performance.now();
        if (this._lastPayoffChangeTime) {
            this.push('_profitHistory', {payoff: oldProfit, time: oldTime});
        }

        // update current profit line y value
        this.currentProfitLine
            .attr('y1', this.yScale(newProfit))
            .attr('y2', this.yScale(newProfit));

        this._updateYScale();
        // this._updateProfitLine();
    }

    _updateYScale() {
        if (!this.mainGroup || !this.startTime) {
            return;
        }

        const self = this;

        const yDomain = this.yScale.domain();
        const yRange = yDomain[1] - yDomain[0];

        // if current profit value is in middle half of current domain, do nothing
        if (this.profit > yDomain[0] + yRange/4 && this.profit < yDomain[1] - yRange/4) {
            return;
        }

        // change y scale
        this.yScale.domain([
            this.profit - yRange/2,
            this.profit + yRange/2
        ]);

        // update y axis
        this.yAxis.scale(this.yScale);
        this.domYAxis.transition()
            .duration(this.animationTime)
            .call(this.yAxis);

        // transition profit history to new y values
        const profitHistory = this.get('_profitHistory');
        this.profitLines.selectAll('line')
            .data(profitHistory)
          .transition()
            .duration(this.animationTime)
            .attr('y1', d => self.yScale(d.payoff))
            .attr('y2', d => self.yScale(d.payoff));

        // transition current profit line to new y value
        this.currentProfitLine.transition()
            .duration(this.animationTime)
            .attr('y1', this.yScale(this.profit))
            .attr('y2', this.yScale(this.profit));
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
            .attr('clip-path', 'url(#lines-clip)')
            .attr('class', 'profit-line')
            .attr('x1', d =>  self.xScale(d.time))
            .attr('x2', (_, i) => self.xScale(i == profitHistory.length-1 ? self._lastPayoffChangeTime : profitHistory[i+1].time))
            .attr('y1', d => self.yScale(d.payoff))
            .attr('y2', d => self.yScale(d.payoff));

        lines
            .attr('x1', d =>  self.xScale(d.time))
            .attr('x2', (_, i) => self.xScale(i == profitHistory.length-1 ? self._lastPayoffChangeTime : profitHistory[i+1].time))
    }

}

window.customElements.define('profit-graph', ProfitGraph);
