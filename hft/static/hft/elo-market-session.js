
import { PolymerElement, html } from './node_modules/@polymer/polymer/polymer-element.js';
import {PlayersOrderBook} from './market-primitives/orderbook.js'
import {scaler} from './util.js'

import './examples/elo-state-selection.js'
import './examples/elo-info-table.js'
import './market-primitives/spread-graph.js'
import './market-primitives/profit-graph.js'
import './market-primitives/profit-graph-fixed.js'
import './market-primitives/stepwise-calculator.js'
import './market-primitives/ws.js'
import './market-primitives/test-inputs.js'

const MIN_BID = 0;
const MAX_ASK = 2147483647;

class MarketSession extends PolymerElement {

    static get template() {
        return html`
        <style>
            :host{
                /* Custom Color Variables */
                --my-bid-fill:#FAFF7F;
                --my-offer-fill:#41EAD4;
                /* Change in spread graph.js interpolateRGB */
                /* Unable to call var(style) within the d3 function */
                --other-bid-fill:#CC8400;
                --other-offer-fill:#00719E;

                --bid-cue-fill:#DEB05C;
                --offer-cue-fill:#5CA4C1;

                --bid-line-stroke:#FCD997;
                --offer-line-stroke:#99E2FF;
                --background-color-white:#FFFFF0;
                --background-color-blue:#4F759B;

                --global-font:monospace;
            }
            spread-graph{
                width:100vw;
                height:20vh;
            }
            profit-graph{
                width:100vw;
                height:45vh;
            }
            profit-graph-fixed{
                width:100vw;
                height:48vh;
            }
            elo-info-table{
                height:35vh;
                width:100vw;
            }
            elo-state-selection{
                height:35vh;
                width:100vw;
            }

            .middle-section-container{
                display: flex;
                flex-direction: row;
                justify-content: flex-start;
                align-items: center;
                font-weight: bold;
                background: var(--background-color-blue) ;
                border-top: 3px solid #ED6A5A;
                border-bottom: 3px solid #ED6A5A;
            }
            .graph-disabled  {
                cursor:not-allowed;
                pointer-events:none;
            }

            // overlay styling and animation
            #overlay{
                background-color:grey;
                opacity:0.3;
            }
            .session-on{
                animation-name: activate-interface;
                animation-duration: 1s;
                animation-fill-mode: forwards;
            }
            .session-off{
                pointer-events:none;
            }
            @keyframes activate-interface {
                100% {
                    pointer-events:all;
                    background-color:transparent;
                    opacity:1;
                }
            }
        </style>
            <ws-connection
                id="websocket"
                url-to-connect={{websocketUrl}}
            ></ws-connection>
            <stepwise-calculator
                run-forever={{subscribesSpeed}}
                value={{speedCost}}
                unit-size={{speedUnitCost}}
                last-step={{previousSpeedCostStep}}
            ></stepwise-calculator>
            <test-inputs
                is-running={{isSessionActive}}
            ></test-inputs>
           
            <div id='overlay' class$='[[_activeSession(isSessionActive)]]'>
                <spread-graph class$='[[_isSpreadGraphDisabled(role)]]' bid-cue={{eBestBid}} offer-cue={{eBestOffer}} orders={{orderBook}} my-bid={{myBid}} 
                    my-offer={{myOffer}} best-bid={{bestBid}} best-offer={{bestOffer}}> </spread-graph>
                <div class="middle-section-container">       
                    <elo-info-table inventory={{inventory}}
                        cash={{cash}} signed-volume={{signedVolume}}
                        endowment={{wealth}} best-bid={{bestBid}}
                        best-offer={{bestOffer}} my-bid={{myBid}} my-offer={{myOffer}}> 
                    </elo-info-table>
                    <elo-state-selection role={{role}} buttons={{buttons}} slider-defaults={{sliderDefaults}}
                        speed-on={{subscribesSpeed}} 
                        manual-button-displayed={{manualButtonDisplayed}} 
                        sv-slider-displayed={{svSliderDisplayed}}> 
                    </elo-state-selection>
                </div>

                <profit-graph
                    profit={{wealth}}
                    is-running={{isSessionActive}}
                    x-range="{{sessionLengthMS}}"
                ></profit-graph>
    
                <!---
                <profit-graph-fixed
                    profit={{wealth}}
                    is-running={{isSessionActive}}
                ></profit-graph-fixed>
                --->
            </div>
    `;
    }
    static get properties() {
      return {
        eventListeners: Object,
        eventHandlers: Object,
        sliderDefaults: Object,
        manualButtonDisplayed:Boolean,
        svSliderDisplayed:Boolean,
        eBestBid: Number,
        eBestOffer: Number,
        eSignedVolume:Number,
        events: Object,
        playerId: Number,
        role: String,
        startRole: String,
        referencePrice: Number,
        signedVolume: {type: Number,
            value: 0},
        orderBook: Object,
        bestBid: Number,
        volumeBestBid: Number,
        bestOffer: Number,
        volumeBestOffer: Number,
        myBid: Number,
        myOffer: Number,
        eBestBid: Number,
        eBestOffer: Number,
        wealth: {
            type: Number,
            computed: '_calculateWealth(cash, speedCost, referencePrice, inventory)'
        },
        inventory: {type: Number,
            value: 0},
        cash: Number,
        speedUnitCost: Number,
        speedCost: {type: Number, value: 0},
        subscribesSpeed: {
            type: Boolean, 
            value: false,
            reflectToAttribute: true
        },
        isSessionActive:{
            type: Boolean,
            value: false,
        },
        sessionLengthMS:{
            type: Number, // milliseconds
            value: OTREE_CONSTANTS.sessionLength * 1e3,
        },
        scaleForDisplay:{
            type: Boolean,
            value: true
        },
        websocketUrl: {
            type: Object,
            value: function () {
                let protocol = 'ws://';
                if (window.location.protocol === 'https:') {
                    protocol = 'wss://';
                    }
                const url = (
                    protocol +
                    window.location.host +
                    '/hft/' +
                    OTREE_CONSTANTS.subsessionId + '/' +
                    OTREE_CONSTANTS.marketId + '/' +
                    OTREE_CONSTANTS.playerId + '/'
                )
                return url
            },
        }
      }
    }

    constructor() {
        super();
        this.orderBook = new PlayersOrderBook(this.playerId, this, 'orderBook');
        //Starting Role
        this.role = 'out';
        this.addEventListener('user-input', this.outboundMessage.bind(this))
        this.addEventListener('inbound-ws-message', this.inboundMessage.bind(this))
    }

    ready(){
        super.ready();
        // we need a proper way to scale initial values
        // maybe a constants component
        this.playerId = OTREE_CONSTANTS.playerId
        this.manualButtonDisplayed = OTREE_CONSTANTS.manualButtonDisplayed
        this.svSliderDisplayed = OTREE_CONSTANTS.svSliderDisplayed
        this.referencePrice = 0
        this.cash = 0
        this.wealth = 0
        this.speedUnitCost = OTREE_CONSTANTS.speedCost * 0.000001
        this.inventory = 0
        this.signedVolume = 0
    }

    outboundMessage(event) {
        const messagePayload = event.detail
        // console.log(messagePayload);
        let cleanMessage = this._msgSanitize(messagePayload, 'outbound')
        if (this.scaleForDisplay) {
            cleanMessage = scaler(cleanMessage, 1)
        }     
        let wsMessage = new CustomEvent('ws-message', {bubbles: true, composed: true, 
            detail: messagePayload })
        this.$.websocket.dispatchEvent(wsMessage)
    }
    
    inboundMessage(event) {
        const messagePayload = event.detail
        // this api is to handle updates as single messages
        // it is also possible to batch these messages for performance
        // and take the exit below.
        // console.log(messagePayload)
        if (messagePayload.type == 'batch'){
            this._handleBatchMessage(messagePayload)
            return
        }
        let cleanMessage = this._msgSanitize(messagePayload, 'inbound')
        if (this.scaleForDisplay) {
            cleanMessage = scaler(cleanMessage, 2)
        }      
        const messageType = cleanMessage.type
        const handlers = this.eventHandlers[messageType]
        for (let i = 0; i < handlers.length; i++) {
            let handlerName = handlers[i]
            this[handlerName](cleanMessage)
        }
    }

    _handleBatchMessage(message) {
        let marketState = {}
        let myState = {'cash': this.cash}
        for (let msg of message.batch) {
            let cleanMsg = this._msgSanitize(msg, 'inbound')
            if (this.scaleForDisplay) {
                cleanMsg = scaler(cleanMsg, 2)
            }    
            switch (cleanMsg.type) {
                case 'bbo':
                    marketState.bestBid = cleanMsg.best_bid
                    marketState.bestOffer = cleanMsg.best_offer
                    marketState.volumeBestBid = cleanMsg.volume_at_best_bid
                    marketState.volumeBestOffer = cleanMsg.volume_at_best_offer
                    break
                case 'signed_volume':
                    marketState.signedVolume = cleanMsg.signed_volume
                    break
                case 'reference_price':
                    marketState.referencePrice = cleanMsg.reference_price
                    break
                case 'external_feed':
                    marketState.eBestBid = cleanMsg.e_best_bid
                    marketState.eBestOffer = cleanMsg.e_best_offer
                    marketState.eSignedVolume = cleanMsg.e_signed_volume
                case 'confirmed':
                case 'replaced':
                case 'executed':
                case 'canceled':
                    this.orderBook.recv(cleanMsg)
            }
            if (cleanMsg.player_id == this.playerId) {
                if (cleanMsg.type == 'executed' || cleanMsg.type == 'cancel') {
                    switch (cleanMsg.buy_sell_indicator) {
                        case 'B':
                            myState.myBid = 0
                            break
                        case 'S':
                            myState.myOffer = 0
                            break
                        }
                    }
                if (cleanMsg.type == 'executed') {
                    myState.inventory = cleanMsg.inventory
                    let cashChange = cleanMsg.buy_sell_indicator == 'B' ?  - cleanMsg.execution_price :
                    cleanMsg.execution_price
                    myState.cash += cashChange
                }
                else if (cleanMsg.type == 'confirmed') {
                    switch (cleanMsg.buy_sell_indicator) {
                        case 'B':
                            myState.myBid = cleanMsg.price
                            break
                        case 'S':
                            myState.myOffer = cleanMsg.price
                            break
                    }
                }
                else if (cleanMsg.type == 'replaced') {
                    switch (cleanMsg.buy_sell_indicator) {
                        case 'B':
                            myState.myBid = cleanMsg.price
                            break
                        case 'S':
                            myState.myOffer = cleanMsg.price
                            break
                    }
                }
            }
        }
        let states = [myState, marketState]
        for (let newState of states) {
            for (let key in newState) {
                // console.log('updateing', key, 'with', newState[key])
                this[key] = newState[key]
            }
        }
        this.notifyPath('orderBook._bidPriceSlots')
    }

    _handleExternalFeed(message){
        this.eBestBid = message.e_best_bid
        this.eBestOffer = message.e_best_offer
        this.eSignedVolume = message.e_signed_volume;
    }
    
    _handleExchangeMessage(message) {
        this.orderBook.recv(message)
        if (message.player_id == this.playerId) {
            let mode = message.type == 'executed' || message.type == 'canceled' ?
                'remove' : 'add'
            this._myBidOfferUpdate(message.price, message.buy_sell_indicator, mode=mode)
        }

        // notify a subproperty 
        // so observer on property is called
        this.notifyPath('orderBook._bidPriceSlots')
    }
    
    _handleExecuted(message) {
        if (message.player_id == this.playerId) {
        let cashChange = message.buy_sell_indicator == 'B' ?  - message.execution_price :
            message.execution_price
        this.cash += cashChange
        this.inventory = message.inventory
        }
    }
    
    _handleBestBidOfferUpdate(message) {
        this.bestBid = message.best_bid
        this.bestOffer = message.best_offer
        this.volumeBestBid = message.volume_at_best_bid
        this.volumeBestOffer = message.volume_at_best_offer
    }

    _handleRoleConfirm(message) {
        if (message.player_id == this.playerId) {
            this.role = message.role_name
        }

    }
    _handleSystemEvent(message) {
        if (message.code == 'S') {
            this.isSessionActive = true
        }
    }

    _handleSpeedConfirm(message){
        if (message.player_id == this.playerId) {
            this.subscribesSpeed = message.value
        }  
    }

    _handleReferencePrice(message) {
        this.referencePrice = message.reference_price
    }

    _handleExternalFeed(message) {
        this.eBestBid = message.e_best_bid
        this.eBestOffer = message.e_best_offer
    }

    _handleSignedVolume(message){
        this.signedVolume = message.signed_volume
    }
    
    _myBidOfferUpdate(price, buySellIndicator, mode='add') {
        switch (buySellIndicator) {
            case 'B':
                this.myBid = mode == 'add' ? price : 0
                break
            case 'S':
                this.myOffer = mode == 'add' ? price : 0
                break
        }
    }

    _activeSession(isActive){
        return (isActive == true) ? 'session-on' : 'session-off';
    }

    _isSpreadGraphDisabled(playerRole){
        return (playerRole == 'manual') ? '' : 'graph-disabled';
    }

    _msgSanitize (messagePayload, direction) {
        if (this.events[direction].hasOwnProperty(messagePayload.type)) {

            let cleanMessage = {}
            let fieldsTypes = this.events[direction][messagePayload.type]
            for (let key in fieldsTypes) {
                let fieldParser = fieldsTypes[key]
                if (!messagePayload.hasOwnProperty(key)) {
                    console.error(`error: ${key} missing in `, messagePayload)
                    return ;
                }

                let rawValue = messagePayload[key]
                if (typeof rawValue == 'undefined' || rawValue === null) {
                    console.error(`invalid value: ${rawValue} for key: ${key}`)
                }

                let cleanValue = fieldParser(rawValue)

                if (typeof cleanValue == 'undefined' || cleanValue === null) {
                    console.error(`parser: ${fieldParser} returned ${cleanValue} `)
                }

                cleanMessage[key] = cleanValue
            }
            return cleanMessage;
        }
        else {
            console.error(`invalid message type: ${messagePayload.type} in `, messagePayload);
        }
    }

    _calculateCost(speedCost) {
        // we should revisit this rounding issue
        // in general we want to integers
        return Math.round(speedCost)
    }

    _calculateWealth(cash, costStep, referencePrice, inventory) {
        const out = Math.round(cash - costStep + referencePrice * inventory) 
        return out
    }

}

customElements.define('elo-market-session', MarketSession)