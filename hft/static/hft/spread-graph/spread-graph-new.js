import {html,PolymerElement}   from '../node_modules/@polymer/polymer/polymer-element.js';

class SpreadGraph extends PolymerElement {

    static get template() {
        return html`
            <style>
                :host {
                    display: block;
                }

                .volumes circle {
                    fill: lightblue;
                    fill-opacity: 0.8;
                    stroke: blue;
                }
            </style>
            
            <svg id="svg"></svg>
        `;
    }

    static get properties() {
        return {
            margin: {
                type: Object,
                value: {top: 40, left: 10, right: 10, bottom: 40},
            },
            orders: {
                type: Array,
                /*
                order book type signature:
                [
                    {
                        price: Number,
                    }
                ]
                */
            },
            animationTime: {
                type: Number,
                value: 200,
            },
            _domain: {
                type: Array,
                value: [100, 110],
            },
        };
    }

    static get observers() {
        return [
            'ordersChanged(orders.splices)',
        ]
    }

    init() {
        this.svg = d3.select(this.$.svg)
            .attr('width', this.offsetWidth)
            .attr('height', this.offsetHeight)
          .append('g')
            .attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');
        
        this.volume_circles = this.svg.append('g')
            .attr('class', 'volumes');
        
        this.scale = d3.scaleLinear()
            .domain(this._domain)
            .range([0, this.width]);
        
        this.xAxis = d3.axisBottom()
            .scale(this.scale);

        this.domXAxis = this.svg.append("g")
            .attr("class", "axis axis--x")
            .attr("transform", "translate(0," + this.height / 2 + ")")
            .call(this.xAxis);
    }

    ordersChanged() {
        const orders = this.get('orders');

        this.updateDomain(orders);
        this.updateScale();        
        this.redrawOrderCircles(orders);
    }

    redrawOrderCircles(orders) {
        if (!this.svg) {
            return;
        }
        
        const volumes = d3.nest()
            .key(d => d.price)
            .rollup(v => v.length)
            .entries(orders);
        
        const circles = this.volume_circles.selectAll('circle')
            .data(volumes, d => d.key);
        
        circles.exit()
            .transition()
            .duration(this.animationTime)
            .attr('r', 0)
            .remove();
        
        const MIN_CIRCLE_RADIUS = 10;

        circles.enter()
            .append('circle')
            .attr('cy', this.height / 2)
            .attr('cx', d => this.scale(d.key))
            .transition()
            .duration(this.animationTime)
            .attr('r', d => d.value * MIN_CIRCLE_RADIUS);
        
        circles.transition()
            .duration(this.animationTime)
            .attr('cx', d => this.scale(d.key))
            .attr('r', d => d.value * MIN_CIRCLE_RADIUS);
    }

    updateDomain(orders) {
        if (!this.svg || !orders.length) {
            return;
        }
        
        const min = d3.min(orders, d => d.price);
        const max = d3.max(orders, d => d.price);

        if (min > this._domain[0] && max < this._domain[1]) {
            return;
        }

        if (max - min < this._min_domain_size) {
            const center = (max + min) / 2;
            this._domain = [
                center - this._min_domain_size / 2,
                center + this._min_domain_size / 2
            ]
        }
        else {
            this._domain = [min, max];
        }
    }

    updateScale() {
        if (!this.svg) {
            return
        }

        this.scale.domain(this._domain);
        this.xAxis.scale(this.scale);
        this.domXAxis.transition()
            .duration(this.animationTime)
            .call(this.xAxis);
    }

    connectedCallback() {
        super.connectedCallback();

        this.width = this.offsetWidth - this.margin.left - this.margin.right;
        this.height = this.offsetHeight - this.margin.top - this.margin.bottom;

        this._min_domain_size = this._domain[1] - this._domain[0];

        this.init();

        this.redrawOrderCircles(this.get('orders'));
    }
}

customElements.define('spread-graph', SpreadGraph);