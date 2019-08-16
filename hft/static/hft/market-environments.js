const ELO = {
    events: {
        inbound:{
            confirmed: {
                type: String,
                order_token: String,
                price: parseInt,
                player_id: String,
                market_id: parseInt,
                buy_sell_indicator: String,
                time_in_force: parseInt
            },
            signed_volume: {
                type: String,
                market_id: parseInt,
                signed_volume: parseFloat
            },
            external_feed: {
                type: String,
                market_id: parseInt,
                e_best_bid: parseInt,
                e_best_offer: parseInt,
                e_signed_volume: parseFloat
            },
            executed: {
                type: String,
                order_token: String,
                player_id: parseInt,
                market_id: parseInt,
                price: parseInt,
                inventory: parseInt,
                execution_price: parseInt,
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
            reference_price: {
                type: String,
                market_id: parseInt,
                reference_price: parseInt
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
            speed_confirm: {
                type: String,
                market_id: parseInt,
                player_id: parseInt,
                value: Boolean
            },
            system_event: {
                type: String,
                market_id: parseInt,
                code: String
            },
            slider_confirm: {
                type: String,
                market_id: parseInt,
                player_id: parseInt,
                a_x: parseFloat,
                a_y: parseFloat,
                a_z: parseFloat
            },
            middle_peg:{
                type:String,
                price: parseFloat,
            },
            post_batch: {
                type: String,
                best_bid: parseInt,
                best_offer: parseInt,
                volume_at_best_bid: parseInt,
                volume_at_best_offer: parseInt,
                clearing_price: parseInt,
                transacted_volume: parseInt,
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
                a_z: parseFloat,
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
        signed_volume: ['_handleSignedVolume'],
        external_feed: ['_handleExternalFeed'],
        elo_quote_cue: ['_handleTakerCue'],
        speed_confirm: ['_handleSpeedConfirm'],
        reference_price: ['_handleReferencePrice'],
        slider_confirm: ['_handleSliderConfirm'],
        mid_peg: ['_handleMiddlePeg'],
    },
    sliderProperties: {
        minValue: 0,
        maxValue: 1,
        stepSize: 0.1
    },
}

export {ELO}