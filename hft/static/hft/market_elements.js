function BBO() {
    this.bestBid = 0;
    this.bestOffer = 2147483647;
    this.volumeBid = 0;
    this.volumeOffer = 0;
}

class PlayersOrderBook {
    constructor() {
        this._bidPriceSlots = {};
        this._offerPriceSlots = {};
        this._bbo = new BBO();
    }

    recv(message) {
        switch(message.type) {
            case 'confirmed':
                this._addOrder(message);
                break;
            case 'executed':
            case 'canceled':
                this._removeOrder(message);
                break;
            case 'replaced':
                this._replaceOrder(message);
            case 'bbo':
                this._bboUpdate(message);
        }
    }

    get bbo() {
        return this._bbo;
    }
    
    getOrders(buySellIndicator) {
        if (buySellIndicator === 'B') {
            return this._bidPriceSlots;
        } else if (buySellIndicator === 'S') {
            return this._offerPriceSlots;
        } else {console.error(`invalid buy sell indicator: ${buySellIndicator}`)}
    }

    _bboUpdate(message) {
        this._bbo.bestBid = message.best_bid;
        this._bbo.bestOffer = message.best_offer;
        this._bbo.volumeBid = message.volume_bid;
        this._bbo.volumeOffer = message.volume_offer;
    }

    _addOrder(message) {
        let priceSlots = this.getOrders(message.buy_sell_indicator)

        if (!priceSlots.hasOwnProperty(message.price)) {
            priceSlots[message.price] = {};
        }

        priceSlots[message.price][message.order_token] = 1;
    }

    _removeOrder(message) {
        let priceSlots = this.getOrders(message.buy_sell_indicator);
        if (!priceSlots.hasOwnProperty(message.price)) {
            console.error(`price ${message.price} is not in ${priceSlots}`)
        } else {
            if (!priceSlots[message.price].hasOwnProperty(message.order_token)) {
                console.error(`order token ${message.order_token} is not in ${priceSlots}`)    
            } else {
                delete priceSlots[message.price][message.order_token]
                if (Object.keys(priceSlots[message.price]).length == 0) {
                    delete priceSlots[message.price];
                }
            }
        }
    }

    _replaceOrder(message) {
        let removeMessage = {order_token: message.old_token, price: message.old_price,
            buy_sell_indicator: message.buy_sell_indicator}
        this._removeOrder(removeMessage);
        this._addOrder(message);
    }
}

export {PlayersOrderBook};