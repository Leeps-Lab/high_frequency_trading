import {html,PolymerElement}   from '../node_modules/@polymer/polymer/polymer-element.js';

class SpreadGraph extends PolymerElement {

    static get template() {
        return html`
            <style>
                :host {
                    display: block;
                }

                * {
                    user-select: none;
                }

                .volume {
                    fill-opacity: 0.8;
                }

                .offer-entered-line, .bid-entered-line {
                    stroke-width: 2;
                    stroke-linecap: round;
                }

                .offer-entered-line {
                    stroke: coral;
                }

                .bid-entered-line {
                    stroke: limegreen;
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
                type: Object,
            },
            animationTime: {
                type: Number,
                value: 200,
            },
            _domain: {
                type: Array,
                value: [100, 110],
            },
            // these two properties define the color gradients used to color volume circles
            // the left color is the color used when a volume circle contains all offers,
            // the right color is used when a circle contains all bids
            _volumeFillGradient: {
                type: Object,
                value: () => d3.interpolateRgb('coral', 'limegreen'),
            },
            _volumeStrokeGradient: {
                type: Object,
                value: () => d3.interpolateRgb('red', 'green'),
            },
        };
    }

    static get observers() {
        return [
            'ordersChanged(orders.*)',
        ];
    }

    connectedCallback() {
        super.connectedCallback();

        this.width = this.offsetWidth - this.margin.left - this.margin.right;
        this.height = this.offsetHeight - this.margin.top - this.margin.bottom;

        this._min_domain_size = this._domain[1] - this._domain[0];

        this.init();

        const orders = this.get('orders');
        if (orders) {
            this.redrawOrderCircles(orders);
        }
    }

    init() {
        this.$.svg.addEventListener('click', e => {
            this.enterOrder(e.offsetX - this.margin.left, 'S');
        });
        this.$.svg.addEventListener('contextmenu', e => {
            e.preventDefault();
            this.enterOrder(e.offsetX - this.margin.left, 'B');
        });

        this.mainGroup = d3.select(this.$.svg)
            .attr('width', this.offsetWidth)
            .attr('height', this.offsetHeight)
          .append('g')
            .attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');
        
        this.volumeCircles = this.mainGroup.append('g');
        this.orderEnteredLines = this.mainGroup.append('g');
        
        this.scale = d3.scaleLinear()
            .domain(this._domain)
            .range([0, this.width]);
        
        this.xAxis = d3.axisBottom()
            .scale(this.scale);

        this.domXAxis = this.mainGroup.append("g")
            .attr("class", "axis")
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
        if (!this.mainGroup) {
            return;
        }

        const self = this;
        
        /*
        transforms order book into an array suitable for use with d3

        volumes = [
            {
                price: `price`
                volume: `volume`,
                bidProportion: `proportion of bids`
            }
        ]

        volume field is the total volume of orders at that price
        bidProportion field is the proportion of volume taken up by bid orders. 1 is all bids, 0 is all offers
        */       
        const prices = d3.set();
        d3.keys(orders._bidPriceSlots).forEach(e => prices.add(e));
        d3.keys(orders._offerPriceSlots).forEach(e => prices.add(e));
        const volumes = [];
        prices.each(price => {
            const bidVolume = d3.values(orders._bidPriceSlots[price]).reduce((a, b) => a + b, 0);
            const offerVolume = d3.values(orders._offerPriceSlots[price]).reduce((a, b) => a + b, 0);
            volumes.push({
                price: price,
                volume: bidVolume + offerVolume,
                bidProportion: bidVolume / (bidVolume + offerVolume)
            });
        });

        const circles = this.volumeCircles.selectAll('circle')
            .data(volumes, d => d.price);
        
        circles.exit()
            .transition()
            .duration(this.animationTime)
            .attr('r', 0)
            .remove();
        
        const MIN_CIRCLE_RADIUS = 10;

        circles.enter()
            .append('circle')
            .attr('cy', this.height / 2)
            .attr('cx', d => this.scale(d.price))
            .attr('class', 'volume')
            .style('fill', d => self._volumeFillGradient(d.bidProportion))
            .style('stroke', d => self._volumeStrokeGradient(d.bidProportion))
          .transition()
            .duration(this.animationTime)
            .attr('r', d => Math.sqrt(d.volume) * MIN_CIRCLE_RADIUS);
        
        circles.transition()
            .duration(this.animationTime)
            .attr('cx', d => this.scale(d.price))
            .attr('r', d => Math.sqrt(d.volume) * MIN_CIRCLE_RADIUS)
            .style('fill', d => self._volumeFillGradient(d.bidProportion))
            .style('stroke', d => self._volumeStrokeGradient(d.bidProportion));
    }

    updateDomain(orders) {
        const prices = d3.keys(orders._bidPriceSlots)
            .concat(d3.keys(orders._offerPriceSlots))
            .map(e => parseFloat(e));
        
        if (!this.mainGroup || !prices.length) {
            return;
        }

        const min = d3.min(prices);
        const max = d3.max(prices);

        // if all prices are contained within the current domain and
        // the price spread takes up at least half of the domain
        // don't change the domain
        if ( (min > this._domain[0] && max < this._domain[1]) &&
             (max - min > (this._domain[1] - this._domain[0]) / 2) ) {
            return;
        }

        // if the price spread is less than the min domain size
        // set domain size to min and center it around avg of max and min
        if (max - min < this._min_domain_size) {
            const center = (max + min) / 2;
            this._domain = [
                center - this._min_domain_size / 2,
                center + this._min_domain_size / 2
            ]
        }
        // otherwise fit domain to max and min of data
        else {
            this._domain = [min, max];
        }
    }

    updateScale() {
        if (!this.mainGroup) {
            return
        }

        const self = this;

        this.scale.domain(this._domain);
        this.xAxis.scale(this.scale);
        this.domXAxis.transition()
            .duration(this.animationTime)
            .call(this.xAxis);
        
        // transition order entered lines to new position
        // use selection.tween hack to get around single transition restriction
        // https://bl.ocks.org/mbostock/5348789
        this.orderEnteredLines.selectAll('line').each(function() {
            const line = d3.select(this);
            const start = this.getAttribute('x1');
            const end = self.scale(this.getAttribute('data-price'));
            if (start == end) return;
            const transitionLock = {};
            d3.select(transitionLock).transition()
                .duration(self.animationTime)
                .tween('attr.position', function() {
                    const i = d3.interpolateNumber(start, end);
                    return function(t) {
                        line.attr('x1', i(t))
                            .attr('x2', i(t));
                    }
                });
        });
    }

    enterOrder(clickX, order_type) {
        const price = Math.round(this.scale.invert(clickX));

        const TRANSITION_TIME = 200;

        this.orderEnteredLines.append('line')
            .attr('class', order_type == 'B' ? 'bid-entered-line' : 'offer-entered-line')
            .attr('data-price', price)
            .attr('x1', this.scale(price))
            .attr('x2', this.scale(price))
            .attr('y1', this.height / 2)
            .attr('y2', this.height / 2)
          .transition()
            .duration(TRANSITION_TIME)
            .attr('y1', 0)
            .attr('y2', this.height)
          .transition()
            .duration(TRANSITION_TIME)
            .style('opacity', 0)
            .remove();

        const orderEnteredEvent = new CustomEvent('user-input', {
            bubbles: true, composed: true, detail: {
                type: 'order_entered',
                price: price,
                buy_sell_indicator: order_type
            }
        })
        this.dispatchEvent(orderEnteredEvent)
    }
}

customElements.define('spread-graph', SpreadGraph);