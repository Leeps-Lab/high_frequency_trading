import {html, PolymerElement}  from '../node_modules/@polymer/polymer/polymer-element.js';

class ProfitGraphFixed extends PolymerElement {

    static get template() {
        return html`
            <style>
                :host {
                    display: block;
                }
                :host #svg{
                    background-color:#FFFFF0;
                }
                .profit-line {
                    stroke: black;
                    stroke-width: 2;
                }
                g text{
                    font-family:monospace;
                    font-size:10px;
                    font-weight: bold; 
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
                value: {top: 40, left: 40, right: 40, bottom: 40},
            },
            xRange: {
                type: Number,
                value: 150000,
            },
            xTimeOffset: {
                type: Number,
                value: 0,
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
                value: [-20, 20],
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

        window.addEventListener('resize', e => {
            this.setSize(this.offsetWidth, this.offsetHeight);
            this._updateProfitLine();
        });

        this.init();
    }

    init() {
        this.mainGroup = d3.select(this.$.svg)
            .append('g')
            .attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');
        this.rightGroup = d3.select(this.$.svg)
            .append('g')
            .attr('transform', 'translate(' + (window.outerWidth - this.margin.right) + ',' + this.margin.top + ')');
        
        this.clipPath = this.mainGroup.append('clipPath')
            .attr('id', 'lines-clip')
          .append('rect');
        
        this.profitLines = this.mainGroup.append('g');

        this.xScale = d3.scaleTime()
            .domain([0, this.xRange]);
        
        this.xAxis = d3.axisBottom()
            .tickFormat(d3.timeFormat('%M:%S'));

        this.domXAxis = this.mainGroup.append("g")
            .attr("class", "axis axis-x");

        this.yScale = d3.scaleLinear()
            .domain(this._defaultYRange);
        
        this.yAxisLeft = d3.axisLeft()
            .tickSize(0);
        this.yAxisRight = d3.axisRight()
            .tickSize(0);

        this.domYAxisRight = this.rightGroup.append("g")
            .attr("class", "axis axis-y");
        this.domYAxisLeft = this.mainGroup.append("g")
            .attr("class", "axis axis-y");
        

        this.currentProfitLine = this.mainGroup.append('line')
            .attr('clip-path', 'url(#lines-clip)')
            .attr('class', 'profit-line');

        this.setSize(this.offsetWidth, this.offsetHeight);
        console.log('profit graph range', this._defaultYRange)
    }

    setSize(width, height) {
        this.width = width - this.margin.left - this.margin.right;
        this.height = height - this.margin.top - this.margin.bottom;

        d3.select(this.$.svg)
            .attr('width', width)
            .attr('height', height);

        this.mainGroup
            .attr('width', this.width)
            .attr('height', this.height);
        this.rightGroup
            .attr('width', (window.outerWidth - this.margin.right))
            .attr('height', this.height);
        
        this.clipPath
            .attr('width', this.width)
            .attr('height', this.height);

        this.xScale.range([0, this.width]);
        this.xAxis.scale(this.xScale);
        this.domXAxis
            .attr("transform", "translate(0," + this.height + ")")
            .call(this.xAxis);

        this.yScale.range([this.height, 0]);
        this.yAxisLeft.scale(this.yScale);
        this.yAxisRight.scale(this.yScale);

        this.domYAxisLeft.call(this.yAxisLeft);
        this.domYAxisRight.call(this.yAxisRight);
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

        if (this.profit) {
            this._addPayoff(this.profit);
        }
        window.setInterval(function(){
        	window.requestAnimationFrame(this._tick.bind(this))
        }.bind(this)
        ,500)
        
    }

    _tick() {
        const now = performance.now()
        if (now > this.startTime + this.xRange) {
            this.xScale.domain([now - this.xRange, now]);
            this.xAxis.scale(this.xScale);
            this.domXAxis.call(this.xAxis);
            this._updateProfitLine();
        }

        this.currentProfitLine
            .attr('x1', this.xScale(this._lastPayoffChangeTime))
            .attr('x2', this.xScale(now));
        //window.requestAnimationFrame(this._tick.bind(this));
    }

    _addPayoff(newProfit, oldProfit) {
        if (!this.mainGroup || !this.startTime) {
            return;
        }

        const oldTime = this._lastPayoffChangeTime;
        this._lastPayoffChangeTime = performance.now();
        if (this._lastPayoffChangeTime) {
            // this.push('_profitHistory', {payoff: oldProfit, time: oldTime, endTime: performance.now()});
            this.push('_profitHistory', {payoff: oldProfit, time: oldTime});

        }

        // update current profit line y value
        this.currentProfitLine
            .attr('y1', this.yScale(newProfit))
            .attr('y2', this.yScale(newProfit))
            .attr('x1', this.xScale(this._lastPayoffChangeTime));

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
        if(this.profit > yDomain[0] + yRange/5 && this.profit < yDomain[1] - yRange/5) {
            return;
        }

        // change y scale
        this.yScale.domain([
            this.profit - yRange/2,
            this.profit + yRange/2
        ]);

        // update y axis
        this.yAxisLeft.scale(this.yScale);
        this.yAxisRight.scale(this.yScale);

        this.domYAxisLeft.transition()
            .duration(this.animationTime)
            .call(this.yAxisLeft);
        this.domYAxisRight.transition()
            .duration(this.animationTime)
            .call(this.yAxisRight);

        // transition profit history to new y values
        const profitHistory = this.get('_profitHistory');
        this.profitLines.selectAll('line')
            .data(profitHistory)
          .transition()
            // .duration(this.animationTime)
            .attr('y1', d => self.yScale(d.payoff))
            .attr('y2', d => self.yScale(d.payoff));

        // transition current profit line to new y value
        this.currentProfitLine.transition()
            // .duration(this.animationTime)
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

window.customElements.define('profit-graph-fixed', ProfitGraphFixed);
