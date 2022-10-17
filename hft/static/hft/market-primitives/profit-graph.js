import {html, PolymerElement}  from '../node_modules/@polymer/polymer/polymer-element.js';

class ProfitGraph extends PolymerElement {

    static get template() {
        return html`
            <style>
                :host {
                    display: block;
                }
                :host #svg{
                    background-color:var(--background-color-white);
                }
                .profit-line {
                    stroke: black;
                    stroke-width: 1.5;
                }
                .grid-lines{
                    stroke: grey;
                    stroke-width: 1;
                }
                .title-text{
                    font-family:var(--global-font);
                    font-size:1.5em;
                    fill:black;
                    opacity:0.2;
                    font-weight: bold; 
                }
                g text{
                    font-family:var(--global-font);
                    font-size:1.2em;
                    font-weight: bold; 
                }

                .batch-marker {
                    stroke: rgba(3, 166, 47, 0.8);
                    stroke-width: 1;
                }
            </style>
            
            <svg id="svg"></svg>
        `;
    }

    static get properties() {
        return {
            profit: {
                type: Number,
                observer: '_addPayoff'
            },
            titleName:String,
            margin: {
                type: Object,
                value: {top: 10, left: 40, right: 40, bottom: 30},
            },
            xRange: {
                type: Number,
                value: 20000,
            },
            xTimeOffset: {
                type: Number,
                value: 2000,
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
                value: [-10, 10],
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
            .attr('transform', 'translate(0,' + this.margin.top + ')');
        
        this.clipPath = this.mainGroup.append('clipPath')
            .attr('id', 'lines-clip')
            .append('rect');
        
        this.profitLines = this.mainGroup.append('g');
        this.batchMarkers = this.mainGroup.append('g')

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

        this.title = this.mainGroup.append("text")
            .attr("class","title-text");

        this.currentProfitLine = this.mainGroup.append('line')
            .attr('clip-path', 'url(#lines-clip)')
            .attr('class', 'profit-line');

        this.setSize(this.offsetWidth, this.offsetHeight);
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
            .attr('width', this.width)
            .attr('height', this.height);
        
        this.clipPath
            .attr('width', this.width)
            .attr('height', this.height);

        this.xScale.range([0, this.width]);
        this.xAxis.scale(this.xScale);
        this.domXAxis
            .attr("transform", "translate(0," + this.height + ")")
            .call(this.xAxis);

        this.mainGroup.selectAll(".title-text")
            .attr("x", (this.width / 2))             
            .attr("y", (this.height / 2))
            .attr("text-anchor", "middle")
            .text(this.titleName);
        this.yScale.range([this.height, 0]);
        this.yAxisLeft.scale(this.yScale);
        this.yAxisRight.scale(this.yScale);

        this.domYAxisLeft.call(this.yAxisLeft);
        this.domYAxisRight
            .attr('transform', 'translate(' + (this.width + this.margin.right) + ',' + 0 + ')')
            .call(this.yAxisRight);
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

        const intervalId = window.setInterval(this._tick.bind(this), 500);
        // stop graph when session is done
        // xrange is set to the session duration in ms. this is a hack but whatever
        window.setTimeout(function() {
            window.clearInterval(intervalId);
        }, this.xRange);
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
            this.push('_profitHistory', {payoff1: oldProfit, payoff2: oldProfit, time: oldTime}); // new profit
            this.push('_profitHistory', {payoff1: oldProfit, payoff2: newProfit, time: this._lastPayoffChangeTime}); // vertical line
        }

        // update current profit line y value
        this.currentProfitLine
            .attr('y1', this.yScale(newProfit))
            .attr('y2', this.yScale(newProfit))
            .attr('x1', this.xScale(this._lastPayoffChangeTime));
        
        // console.log(newProfit, oldProfit);
        this._updateYScale();
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
            // .duration(this.animationTime)
            .call(this.yAxisLeft);
        this.domYAxisRight.transition()
            // .duration(this.animationTime)
            .call(this.yAxisRight);
       
        // transition profit history to new y values
        const profitHistory = this.get('_profitHistory');
        this.profitLines.selectAll('line')
            .data(profitHistory)
          .transition()
            // .duration(this.animationTime)
            .attr('y1', d => self.yScale(d.payoff1))
            .attr('y2', d => self.yScale(d.payoff2));


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
            .attr('y1', d => self.yScale(d.payoff1))
            .attr('y2', d => self.yScale(d.payoff2));

        lines
            .attr('x1', d =>  self.xScale(d.time))
            .attr('x2', (_, i) => self.xScale(i == profitHistory.length-1 ? self._lastPayoffChangeTime : profitHistory[i+1].time))
    }

    addBatchMarker() {
        const now = performance.now();
        this.batchMarkers.append('line')
            .attr('class', 'batch-marker')
            .attr('x1', this.xScale(now))
            .attr('x2', this.xScale(now))
            .attr('y1', 0)
            .attr('y2', this.height);
    }

}

window.customElements.define('profit-graph', ProfitGraph);
