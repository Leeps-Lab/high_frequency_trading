import {html,PolymerElement}   from '../node_modules/@polymer/polymer/polymer-element.js';

class SpreadGraph extends PolymerElement {

    static get template() {
        return html`
            <style>
                :host {
                    display: block;
                }
                :host #svg{
                    background-color:var(--background-color-white);
                }
                * {
                    user-select: none;
                }
               
                .my-bid {
                    stroke-width: 7;
                    fill: var(--my-bid-fill);
                    fill-opacity: 0.8;
                }

                .my-offer {
                    stroke-width: 7;
                    fill: var(--my-offer-fill);
                    fill-opacity: 0.8;
                }

                .best-bid {
                    stroke-width: 5;
                }

                .best-offer {
                    stroke-width: 5;
                }

                .offer-entered-line, .bid-entered-line {
                    stroke-width: 2;
                    stroke-linecap: round;
                }

                .offer-entered-line {
                    stroke: var(--offer-line-stroke);
                }

                .bid-entered-line {
                    stroke: var(--bid-line-stroke);
                }

                .tick text {
                    font-family:var(--global-font);
                    font-size:14px;
                    font-weight: bold;
                }
                .bid-cue{
                    fill:var(--bid-cue-fill);
                    border:none;
                }
                .offer-cue{
                    fill:var(--offer-cue-fill);
                    border:none;
                }
                .clearing-price-circle{
                    stroke:green;
                    fill:none;
                    stroke-width:5px;
                }
                .mid-peg-line{
                    stroke:black;
                    stroke-width:5px;
                }
            </style>
            <svg id="svg"></svg>
        `;
    }

    static get properties() {
        return {
            margin: {
                type: Object,
                value: {top: 40, left: 15, right: 15, bottom: 40},
            },
            orders: {
                type: Object,
            },
            clearingPrice:{
                type: Object,
                value: {price:0, volume:0},
                observer: 'drawClearingPrice',
            },
            midPeg: {
                type: Number,
                value: 0,
                observer: 'drawMidPeg',
            },
            myBid: {
                type: Number,
                value: 0,
                observer: 'drawMyBid',
            },
            myOffer: {
                type: Number,
                value: 100001,
                observer: 'drawMyOffer',
            },
            bestBid: {
                type: Number,
                value: 0,
            },
            bestOffer: {
                type: Number,
                value: 0,
            },
            bidCue: {
                type: Number,
                value: 0,
                observer: 'drawBidCue',
            },
            offerCue: {
                type: Number,
                value: 0,
                observer: 'drawOfferCue',
            },
            animationTime: {
                type: Number,
                value: 200,
            },
            minVolumeRadius: {
                type: Number,
                value: 10,
            },
            _domainWidth: {
                type: Number,
                value: 20,
            },
            _domain: {
                type: Array,
                value: [90, 110],
            },
            // these two properties define the color gradients used to color volume circles
            // the left color is the color used when a volume circle contains all offers,
            // the right color is used when a circle contains all bids
            _volumeFillGradient: {
                type: Object,
                value: () => d3.interpolateRgb('#00719E', '#CC8400'),
            },
            _volumeStrokeGradient: {
                type: Object,
                value: () => d3.interpolateRgb('#00719E', '#CC8400'),
            },
            // TODO: ali - fill this with correct max offer value
            _MAX_OFFER: {
                type: Number,
                value: 100000,
            }
        };
    }

    static get observers() {
        return [
            'ordersChanged(orders.*)',
            'bestBidOrOfferChanged(bestBid, bestOffer)',
        ];
    }

    connectedCallback() {
        super.connectedCallback();

        window.addEventListener('resize', e => {
            this.setSize(this.offsetWidth, this.offsetHeight);

            const orders = this.get('orders');
            if (orders) {
                this.redrawOrderCircles(orders);
            }
            this.drawMyBid(this.myBid, this.myBid);
            this.drawMyOffer(this.myOffer, this.myOffer);
            this.drawClearingPrice(this.clearingPrice, this.clearingPrice);
            this.drawMidPeg(this.midPeg, this.midPeg)
        });

        this.init();

        const orders = this.get('orders');
        if (orders) {
            this.redrawOrderCircles(orders);
        }
    }

    init() {
        this.$.svg.addEventListener('click', e => {
            this.enterOrder(e.offsetX - this.margin.left, 'B');
        });
        this.$.svg.addEventListener('contextmenu', e => {
            e.preventDefault();
            this.enterOrder(e.offsetX - this.margin.left, 'S');
        });

        this.mainGroup = d3.select(this.$.svg)
          .append('g')
            .attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');
        
        this.volumeCircles = this.mainGroup.append('g');
        this.orderEnteredLines = this.mainGroup.append('g');

        const mainObjectGroup = this.mainGroup.append('g');
        this.myBidCircle = mainObjectGroup.append('circle')
            .attr('class', 'my-bid')
            .attr('r', this.minVolumeRadius)
            .style('opacity', 0);
        this.myOfferCircle = mainObjectGroup.append('circle')
            .attr('class', 'my-offer')
            .attr('r', this.minVolumeRadius)
            .style('opacity', 0);
        this.bidCueCircle = mainObjectGroup.append('circle')
            .attr('class', 'bid-cue')
            .attr('r', 0.75 * this.minVolumeRadius)
            .style('opacity', 0);
        this.offerCueCircle = mainObjectGroup.append('circle')
            .attr('class', 'offer-cue')
            .attr('r', 0.75 * this.minVolumeRadius)
            .style('opacity', 0);

        this.clearingPriceCircle = mainObjectGroup.append('circle')
            .attr('class', 'clearing-price-circle')
            .style('opacity', 0);
        
        this.midPointpeg = mainObjectGroup.append('line')
            .attr('class', 'mid-peg-line');

        this.scale = d3.scaleLinear()
            .domain(this._domain);
        
        this.xAxis = d3.axisBottom()
            .ticks(this._domainWidth);

        this.domXAxis = this.mainGroup.append("g")
            .attr("class", "axis");

        this.setSize(this.offsetWidth, this.offsetHeight);
    }

    setSize(width, height) {
        this.width = width - this.margin.left - this.margin.right;
        this.height = height - this.margin.top - this.margin.bottom;

        d3.select(this.$.svg)
            .attr('width', width)
            .attr('height', height);

        this.myBidCircle.attr('cy', this.height / 2);
        this.myOfferCircle.attr('cy', this.height / 2);
        
        this.bidCueCircle.attr('cy', this.height/50);
        this.offerCueCircle.attr('cy', this.height/50);

        this.clearingPriceCircle.attr('cy', this.height/2)
        this.scale.range([0, this.width]);

        this.xAxis
            .tickSize(this.height / 4)
            .scale(this.scale);

        this.domXAxis
            .attr("transform", "translate(0," + this.height / 2 + ")")
            .call(this.xAxis);
    }

    ordersChanged() {
        const orders = this.get('orders');

        this.updateScale();        
        this.redrawOrderCircles(orders);

        this.drawMyBid(this.myBid, this.myBid);
        this.drawMyOffer(this.myOffer, this.myOffer);
        this.drawBidCue(this.bidCue, this.bidCue);
        this.drawOfferCue(this.offerCue, this.offerCue);
    }

    bestBidOrOfferChanged(bestBid, bestOffer) {
        this.updateDomain(bestBid, bestOffer);
        this.updateScale();

        const orders = this.get('orders');
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
        const prices = {};
        function getDefaultPriceEntry() {
            return {
                bidVolume: 0,
                askVolume: 0,
            };
        }
        d3.values(this.orders._buyOrders)
          .filter(e => e.visible)
          .forEach(e => {
            prices[e.price] = prices[e.price] || getDefaultPriceEntry();
            prices[e.price].bidVolume++;
          });
        d3.values(this.orders._sellOrders)
          .filter(e => e.visible)
          .forEach(e => {
            prices[e.price] = prices[e.price] || getDefaultPriceEntry();
            prices[e.price].askVolume++;
          });

        const volumes = [];
        d3.keys(prices).forEach(price => {
            const bidVolume = prices[price].bidVolume;
            const askVolume = prices[price].askVolume;
            volumes.push({
                price: price, 
                volume: bidVolume + askVolume,
                bidProportion: bidVolume / (bidVolume + askVolume),
            })
        });

        // const prices = d3.set();
        // d3.keys(orders._bidPriceSlots).forEach(e => prices.add(e));
        // d3.keys(orders._offerPriceSlots).forEach(e => prices.add(e));
        // const volumes = [];
        // prices.each(price => {
        //     const bidVolume = d3.values(orders._bidPriceSlots[price]).reduce((a, b) => a + b, 0);
        //     const offerVolume = d3.values(orders._offerPriceSlots[price]).reduce((a, b) => a + b, 0);
        //     volumes.push({
        //         price: price,
        //         volume: bidVolume + offerVolume,
        //         bidProportion: bidVolume / (bidVolume + offerVolume)
        //     });
        // });

        // function to assign classes to volume circles
        function getClass(d) {
            if (d.price == self.bestBid)
                return 'volume best-bid';
            else if (d.price == self.bestOffer)
                return 'volume best-offer';
            else
                return 'volume';
        }

        const circles = this.volumeCircles.selectAll('circle')
            .data(volumes, d => d.price);
        
        circles.exit()
            .transition()
            .duration(this.animationTime)
            .attr('r', 0)
            .remove();
        
        circles.enter()
            .append('circle')
            .attr('cy', this.height / 2)
            .attr('cx', d => this.scale(d.price))
            .attr('class', getClass)
            .style('fill', d => self._volumeFillGradient(d.bidProportion))
            .style('stroke', 'black')
          .transition()
            .duration(this.animationTime)
            .attr('r', d => Math.sqrt(d.volume) * self.minVolumeRadius);
        
        circles.transition()
            .duration(this.animationTime)
            .attr('cx', d => this.scale(d.price))
            .attr('r', d => Math.sqrt(d.volume) * self.minVolumeRadius)
            .attr('class', getClass)
            .style('fill', d => self._volumeFillGradient(d.bidProportion))
            .style('stroke', 'black');
    }

    drawClearingPrice(newCPObj, oldCPObj){
        if (!this.mainGroup) {
            return;
        }
        if (newCPObj["price"] === 0) {
            this.clearingPriceCircle.transition()
                .duration(this.animationTime)
                .style('opacity', 0);
        }
        else {
            if (oldCPObj['price'] === 0) {
                this.clearingPriceCircle
                    .attr('r', Math.sqrt(newCPObj["volume"]) * this.minVolumeRadius)
                    .attr('cx', this.scale(newCPObj["price"]))
                    .attr('cy', this.height/2)
                    .transition()
                    .duration(this.animationTime)
                    .style('opacity', 1);
            }
            else {
                this.clearingPriceCircle.transition()
                    .duration(this.animationTime)
                    .attr('cx', this.scale(newCPObj["price"]))
                    .attr('cy', this.height/2)
                    .attr('r', Math.sqrt(newCPObj["volume"]) * this.minVolumeRadius)
                    .style('opacity', 1);
            }
        }
    }

    drawMidPeg(newMP, oldMP){
        if (!this.mainGroup) {
            return;
        }
        if (newMP === 0) {
            this.midPointpeg.transition()
                .duration(this.animationTime)
                .style('opacity', 0);
        }
        else {
            if (oldMP === 0) {
                this.midPointpeg
                    .attr('x1', this.scale(newMP))
                    .attr('x2', this.scale(newMP))
                    .attr('y1', 0)
                    .attr('y2', this.height)
                    .transition()
                    .duration(this.animationTime)
                    .style('opacity', 1);
            }
            else {
                this.midPointpeg
                    .transition()
                    .duration(this.animationTime)
                    .attr('x1', this.scale(newMP))
                    .attr('x2', this.scale(newMP))
                    .attr('y1', 0)
                    .attr('y2', this.height)
                    .style('opacity', 1);
            }
        }
    }

    drawMyBid(newBid, oldBid) {
        if (!this.mainGroup) {
            return;
        }

        if (newBid === 0) {
            this.myBidCircle.transition()
                .duration(this.animationTime)
                .style('opacity', 0);
        }
        else {
            if (oldBid === 0) {
                this.myBidCircle
                    .attr('cx', this.scale(newBid))
                    .transition()
                    .duration(this.animationTime)
                    .style('opacity', 1);
            }
            else {
                this.myBidCircle.transition()
                    .duration(this.animationTime)
                    .attr('cx', this.scale(newBid))
                    .style('opacity', 1);
            }
        }
    }

    drawMyOffer(newOffer, oldOffer) {
        if (!this.mainGroup) {
            return;
        }

        if (newOffer > this._MAX_OFFER) {
            this.myOfferCircle.transition()
                .duration(this.animationTime)
                .style('opacity', 0);
        }
        else {
            if (oldOffer > this._MAX_OFFER) {
                this.myOfferCircle
                    .attr('cx', this.scale(newOffer))
                    .transition()
                    .duration(this.animationTime)
                    .style('opacity', 1);
            }
            else {
                this.myOfferCircle.transition()
                    .duration(this.animationTime)
                    .attr('cx', this.scale(newOffer))
                    .style('opacity', 1);
            }
        }
    }

    drawBidCue(newBid, oldBid) {

        if (!this.mainGroup) {
            return;
        }

        if (newBid  > this._MAX_OFFER) {
            this.bidCueCircle.transition()
                .duration(this.animationTime)
                .style('opacity', 0);
            
        }
        else {
            if (oldBid === 0) {
                this.bidCueCircle
                    .attr('cx', this.scale(newBid))
                    .transition()
                    .duration(this.animationTime)
                    .style('opacity', 1);
              
            }
            else {
                this.bidCueCircle.transition()
                .duration(this.animationTime)
                .attr('cx', this.scale(newBid))
                .style('opacity', 1);
            }
        }
    }

    drawOfferCue(newOffer, oldOffer) {

        if (!this.mainGroup) {
            return;
        }

        if (newOffer > this._MAX_OFFER) {
            this.offerCueCircle.transition()
                .duration(this.animationTime)
                .style('opacity', 0);
        }
        else {
            if (oldOffer === 0) {
                this.offerCueCircle
                    .attr('cx', this.scale(newOffer))
                    .transition()
                    .duration(this.animationTime)
                    .style('opacity', 1);
            }
            else {
                this.offerCueCircle.transition()
                    .duration(this.animationTime)
                    .attr('cx', this.scale(newOffer))
                    .style('opacity', 1);
            }
        }
    }

    updateDomain(bestBid, bestOffer) {
        if (!this.mainGroup) {
            return;
        }

        // if both best bid and best offer don't exist
        if (bestBid == 0 && bestOffer >= this._MAX_OFFER) {
            return;
        }

        let center;
        // if best bid exists and best offer doesn't
        if (bestBid == 0 && bestOffer < this._MAX_OFFER) {
            center = bestOffer;
        }
        // if best offer exists and best offer doesn't
        else if (bestBid > 0 && bestOffer >= this._MAX_OFFER) {
            center = bestBid;
        }
        // if both best bid and best offer exist
        else {
            center = (bestBid + bestOffer) / 2;
        }

        // if bbo center is contained within the center 80% of current domain, don't change domain
        if (center > this._domain[0] + this._domainWidth*0.2 &&
            center < this._domain[1] - this._domainWidth*0.2) {
                return;
        }

        this._domain = [
            center - this._domainWidth*0.5,
            center + this._domainWidth*0.5,
        ];

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
        // prevent entering an order that self-crosses
        if ( (this.myBid && order_type == 'S' && price <= this.myBid) ||
             (this.myOffer && order_type == 'B' && price >= this.myOffer) ) {
                 return;
        }

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
                buy_sell_indicator: order_type,
                midpoint_peg: false,
            }
        })
        this.dispatchEvent(orderEnteredEvent)
    }
}

customElements.define('spread-graph', SpreadGraph);