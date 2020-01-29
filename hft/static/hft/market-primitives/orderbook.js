
class PlayersOrderBook {

    constructor(playerId) {
        // this.polymerObject = polymerObject;
        // this.polymerPropertyName = polymerPropertyName;

        this.playerId = playerId
        this.auctionFormat = OTREE_CONSTANTS.auctionFormat
        this._buyOrders = {}
        this._sellOrders = {}
        /*
            _orders = {
                `orderToken`: {
                    price: ...,
                    playerId: ...,
                    active: ...,
                }
            }
        */
    }

    recv(message) {
        switch(message.type) {
            case 'confirmed':
                this._addOrder(message.price, message.buy_sell_indicator, 
                    message.order_token, message.player_id, message.time_in_force);
                break;
            case 'executed':
            case 'canceled':
                this._removeOrder(message.price, message.buy_sell_indicator, 
                    message.order_token, message.player_id);
                break;
            case 'replaced':
                this._replaceOrder(message.price, message.buy_sell_indicator, 
                    message.order_token, message.player_id, message.old_price,
                    message.old_token)
                break;
        }
    }

    // handle a post-batch message arriving
    // this is only ever called for FBA auction format
    handlePostBatch() {
        // mark all orders as active
        // and delete orders which have been marked as removed
        for (let order in this._buyOrders) {
            if (this._buyOrders[order].removed) {
                delete this._buyOrders[order];
            }
            else {
                this._buyOrders[order].visible = true;
            }
        }
        for (let order in this._sellOrders) {
            if (this._sellOrders[order].removed) {
                delete this._sellOrders[order];
            }
            else {
                this._sellOrders[order].visible = true;
            }
        }
    }

    getOrders(buySellIndicator) {
        if (buySellIndicator == 'B') {
            return this._buyOrders;
        }
        else {
            return this._sellOrders;
        }
    }

    // returns true if a change in an order from player with id `playerId` should be immediately shown
    _orderIsVisible(playerId) {
        return this.auctionFormat != 'FBA' || playerId == this.playerId;
    }

    _addOrder(price, buySellIndicator, orderToken, playerId, timeInForce=9999) {
        if (timeInForce == 0) {
            return
        }

        const visible = this._orderIsVisible(playerId);
        const order = {
            price: price,
            playerId: playerId,
            visible: visible,
            removed: false,
        }

        if (buySellIndicator == 'B') {
            this._buyOrders[orderToken] = order;
        }
        else {
            this._sellOrders[orderToken] = order;
        }
    }

    _removeOrder(price, buySellIndicator, orderToken, playerId) {
        let orders = this.getOrders(buySellIndicator);
        if (!orders.hasOwnProperty(orderToken)) {
            console.warn(`remove failed: order token ${orderToken} not found`);
            return;
        }
        if (this._orderIsVisible(playerId)) {
            delete orders[orderToken]
        }
        else {
            orders[orderToken].removed = true;
        }
    }

    _replaceOrder(price, buySellIndicator, orderToken, playerId, oldPrice, oldToken) {
        this._removeOrder(oldPrice, buySellIndicator, oldToken, playerId);
        this._addOrder(price, buySellIndicator,  orderToken, playerId);
    }
}

export {PlayersOrderBook};