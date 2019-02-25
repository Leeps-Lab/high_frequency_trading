const ELO = {

    events: {
        inbound:{
            confirmed: {
                type: String,
                order_token: String,
                price: parseInt,
                player_id: String,
                market_id: parseInt,
                buy_sell_indicator: String
            },
            executed: {
                type: String,
                order_token: String,
                player_id: parseInt,
                market_id: parseInt,
                price: parseInt,
                inventory: parseInt,
                cash: parseInt,
                buy_sell_indicator: String
            },
            replaced: {
                type: String,
                order_token: String,
                old_token: String,
                player_id: parseInt,
                market_id: parseInt,
                price: parseInt,
                old_price: parseInt,
                buy_sell_indicator: String
            },
            canceled: {
                type: String,
                order_token: String,
                player_id: parseInt,
                market_id: parseInt,
                price: parseInt,
                buy_sell_indicator: String
            },
            bbo: {
                type: String,
                market_id: parseInt,
                best_bid: parseInt,
                best_offer: parseInt,
                volume_at_best_bid: parseInt,
                volume_at_best_offer: parseInt
            },
            order_imbalance: {
                type: String,
                market_id: parseInt,
                value: parseFloat
            },
            elo_quote_cue: {
                type: String,
                market_id: parseInt,
                bid: parseInt,
                offer: parseInt
            },
            role_confirm: {
                type: String,
                market_id: parseInt,
                player_id: parseInt,
                role_name: String
            },
            system_event: {
                type: String,
                market_id: parseInt,
                code: String
            }
        },
        outbound: {
            order_entered: {
                type: String,
                price: parseInt,
                buy_sell_indicator: String,
            },
            role_change: { 
                type: String,
                state: String,
            }, 
            slider: { 
                type: String,
                a_x: parseFloat,
                a_y: parseFloat,
            },
            speed_change: { 
                type: String,
                value: Boolean,
            },
            player_ready: {
                type: String
            }
        },
    },
    eventHandlers: {
        confirmed: ['_handleExchangeMessage'],
        replaced: ['_handleExchangeMessage'],
        executed: ['_handleExchangeMessage', '_handleExecuted'],
        canceled: ['_handleExchangeMessage'],
        bbo: ['_handleBestBidOfferUpdate'],
        role_confirm: ['_handleRoleConfirm'],
        system_event: ['_handleSystemEvent'],
        order_imbalance: ['_handleOrderImbalance'],
        elo_quote_cue: ['_handleTakerCue']
    },
    sliderProperties: {
        minValue: 0,
        maxValue: 10,
        stepSize: 0.1
    }

}

export {ELO}