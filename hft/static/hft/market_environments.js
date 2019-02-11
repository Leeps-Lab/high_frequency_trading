const ELO = {

    events: {
        inbound:{
            confirmed: {
                type: String,
                order_token: String,
                price: parseInt,
                player_id: String,
                buy_sell_indicator: String
            },
            executed: {
                type: String,
                order_token: String,
                player_id: parseInt,
                price: parseInt,
                inventory: parseInt,
                endowment: parseInt,
                buy_sell_indicator: String
            },
            replaced: {
                type: String,
                order_token: String,
                old_token: String,
                player_id: parseInt,
                price: parseInt,
                old_price: parseInt,
                buy_sell_indicator: String
            },
            canceled: {
                type: String,
                order_token: String,
                player_id: parseInt,
                price: parseInt,
                buy_sell_indicator: String
            },
            bbo: {
                type: String,
                best_bid: parseInt,
                best_offer: parseInt,
                volume_bid: parseInt,
                volume_offer: parseInt
            }
        },
        outbound: {},
    },
    eventHandlers: {
        confirmed: ['_handleExchangeMessage'],
        replaced: ['_handleExchangeMessage'],
        executed: ['_handleExchangeMessage', '_handleExecuted'],
        canceled: ['_handleExchangeMessage'],
        bbo: ['_handleBestBidOfferUpdate']
    }
}

export {ELO}