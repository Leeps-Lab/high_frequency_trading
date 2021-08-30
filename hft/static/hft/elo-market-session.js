
import { PolymerElement, html } from './node_modules/@polymer/polymer/polymer-element.js';
import {PlayersOrderBook} from './market-primitives/orderbook.js'
import {scaler} from './util.js'

import './examples/elo-state-selection.js'
import './examples/elo-info-table.js'
import './market-primitives/spread-graph.js'
import './market-primitives/profit-graph.js'
import './market-primitives/attribute-graph.js'
import './market-primitives/stepwise-calculator.js'
import './market-primitives/ws.js'
import './market-primitives/test-inputs.js'

const MIN_BID = 0;
const MAX_ASK = 2147483647;

let avgLatency = 0;
let sumLatency = 0;
let numPings = 0;

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

                /*Background Color for sliders and on the attirbute graph*/
                --inv-color:#7DB5EC;
                --sv-color:#90ED7D;
                --ef-color:#8980F5;

                --global-font:monospace;
            }
            spread-graph{
                width:100vw;
                height:20vh;
            }
            profit-graph{
                width:100vw;
                height:29vh;
            }
            attribute-graph{
                width:100vw;
                height:15vh;
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
                border-top: 3px solid black;
                border-bottom: 3px solid black;
                /*border-top: 3px solid #ED6A5A;
                border-bottom: 3px solid #ED6A5A;*/
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

            #session_complete_indicator {
                display: none;
                position: fixed;
                right: 20px;
                top: 20px;
                border: 1px solid black;
                background-color: white;
                color: red;
                padding: 5px;
            }
        </style>
            <ws-connection
                id="websocket"
                url-to-connect={{websocketUrl}}
            ></ws-connection>
            <stepwise-calculator
                id="stepwise_calculator"
                run-forever={{subscribesSpeed}}
                value={{speedCost}}
                unit-size={{speedUnitCost}}
                last-step={{previousSpeedCostStep}}
            ></stepwise-calculator>
            <test-inputs
                is-running={{isSessionActive}}
            ></test-inputs>

            <div id="session_complete_indicator">
                Session complete. The page will be advanced shortly.
            </div>
           
            <div id='overlay' class$='[[_activeSession(isSessionActive)]]'>
                <spread-graph class$='[[_isSpreadGraphDisabled(role)]]' 
                    bid-cue={{eBestBid}} offer-cue={{eBestOffer}} 
                    orders={{orderBook}} my-bid={{myBid}} 
                    my-offer={{myOffer}} 
                    best-bid={{bestBid}} best-offer={{bestOffer}}
                    clearing-price={{clearingPrice}}
                    mid-peg={{middlePeg}}> </spread-graph>
                <div class="middle-section-container">       
                    <elo-info-table id="infotable" inventory={{inventory}}
                        cash={{cash}} signed-volume={{signedVolume}}
                        endowment={{wealth}} best-bid={{bestBid}}
                        best-offer={{bestOffer}} my-bid={{myBid}} my-offer={{myOffer}}
                        sv-slider-displayed={{svSliderDisplayed}} clearing-price={{clearingPrice}}>
                    </elo-info-table>
                    <elo-state-selection role={{role}} buttons={{buttons}} slider-defaults={{sliderDefaults}}
                        speed-on={{subscribesSpeed}} 
                        manual-button-displayed={{manualButtonDisplayed}} 
                        sv-slider-displayed={{svSliderDisplayed}}> 
                    </elo-state-selection>
                </div>
                <attribute-graph
                    title-name="Sensitivies"
                    speed-on={{subscribesSpeed}}
                    a_x={{sliderValues.a_x}}
                    a_y={{sliderValues.a_y}}
                    a_z={{sliderValues.a_z}}
                    role={{role}}
                    sv-slider-displayed={{svSliderDisplayed}}
                    is-running={{isSessionActive}}
                    x-range="{{sessionLengthMS}}"
                ></attribute-graph>
                <profit-graph
                    title-name="PBD"
                    profit={{wealth}}
                    is-running={{isSessionActive}}
                    x-range="{{sessionLengthMS}}"
                ></profit-graph>
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
        clearingPrice: Object,
        middlePeg: {
            type: Number,
            computed: '_computeMiddlePeg(eBestBid, eBestOffer)',
        },
        wealth: {
            type: Number,
            computed: '_calculateWealth(cash, speedCost, referencePrice, inventory)'
        },
        inventory: {
            type: Number,
            value: 0
        },
        cash: Number,
        speedUnitCost: Number,
        speedCost: {type: Number, value: 0},
        subscribesSpeed: {
            type: Boolean, 
            reflectToAttribute: true
        },
        sliderValues:{
            type: Object,
            value: {a_x: 0,a_y: 0, a_z:0}
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
        },
      }
    }

    constructor() {
        super();
        this.addEventListener('user-input', this.outboundMessage.bind(this))
        this.addEventListener('inbound-ws-message', this.inboundMessage.bind(this))
        this.addEventListener('inbound-ws-message', this.pingMessage.bind(this))
    }

    ready(){
        super.ready();
        // we need a proper way to scale initial values
        // maybe a constants component
        this.playerId = OTREE_CONSTANTS.playerId
        this.manualButtonDisplayed = OTREE_CONSTANTS.manualButtonDisplayed
        this.svSliderDisplayed = OTREE_CONSTANTS.svSliderDisplayed;
        const initialStrategy = OTREE_CONSTANTS.initialStrategy;
        this.role = initialStrategy.role;
        this.subscribesSpeed = initialStrategy.speed_on;
        this.referencePrice = 0
        this.cash = 100
        this.wealth = 100
        this.speedUnitCost = OTREE_CONSTANTS.speedCost * 0.000001
        this.inventory = 0
        this.signedVolume = 0
        this.orderBook = new PlayersOrderBook(this.playerId);
        this.profitGraph = this.shadowRoot.querySelector('profit-graph')

        this.potentiallyAggressiveOrders = new Set()

        // Testing for ping
        setInterval(this.calcPing.bind(this), 10000);
    }

    calcPing(event) {
        var port = "";
        if (window.location.port.length > 0) {
            port = ':' + window.location.port;
        }
        var url = location.protocol + '//' + window.location.hostname + port + '/ping/';
        
        var t0 = performance.now();
        fetch(url).then(function() {
            var t1 = performance.now();
            var ping = 'Latency: ' + (t1-t0).toFixed(2) + 'ms';
            
            numPings += 1;
            sumLatency += (t1-t0);
            avgLatency = (sumLatency / numPings);
            console.log(ping);
        }).catch((error) => {
            console.error(error);
        });
    }

    pingMessage(event) {
        this.$.websocket.socket.send(JSON.stringify({type: 'ping', avgLatency: avgLatency}));
    }

    outboundMessage(event) {
        const messagePayload = event.detail
        let cleanMessage = this._msgSanitize(messagePayload, 'outbound')
        if (this.scaleForDisplay) {
            cleanMessage = scaler(cleanMessage, 1)
        }     
        let wsMessage = new CustomEvent('ws-message', {bubbles: true, composed: true, 
            detail: cleanMessage })
        this.$.websocket.dispatchEvent(wsMessage)
    }

    inboundMessage(event) {
        const messagePayload = event.detail
        // this api is to handle updates as single messages
        // it is also possible to batch these messages for performance
        // and take the exit below.
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
        const transactions = []
        for (let msg of message.batch) {
            let cleanMsg = this._msgSanitize(msg, 'inbound')
            if (!cleanMsg) {
                continue;
            }
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
                case 'executed':
                    if (cleanMsg.player_id == this.playerId) {  
                        const aggressive = this.potentiallyAggressiveOrders.delete(cleanMsg.order_token)
                        const side = cleanMsg.buy_sell_indicator == 'B' ? 'bid' : 'ask'
                        transactions.push({
                            side: side,
                            aggressive: aggressive
                        })
                    }
                case 'replaced':
                case 'canceled':
                    this.orderBook.recv(cleanMsg)
                    break;
                case 'confirmed':  
 
                    if(cleanMsg.player_id == this.playerId) {
                        if((cleanMsg.buy_sell_indicator == 'B' && cleanMsg.price >= this.bestOffer) || (cleanMsg.buy_sell_indicator == 'S' && cleanMsg.price <= this.bestBid)) {
                            this.potentiallyAggressiveOrders.add(cleanMsg.order_token)
                            setTimeout(()=> {
                                this.potentiallyAggressiveOrders.delete(cleanMsg.order_token)
                            },
                            500)
                        }
                    }
                    this.orderBook.recv(cleanMsg)
                    break;

                case 'post_batch':
                    marketState.bestBid = cleanMsg.best_bid;
                    marketState.bestOffer = cleanMsg.best_offer;
                    marketState.volumeBestBid = cleanMsg.volume_at_best_bid
                    marketState.volumeBestOffer = cleanMsg.volume_at_best_offer
                    marketState.clearingPrice = {
                        price: cleanMsg.clearing_price,
                        volume: cleanMsg.transacted_volume,
                    }
                    this.orderBook.handlePostBatch();
                    //this.profitGraph.addBatchMarker();

                    // Event to trigger clearing info box to animate
                    let event = new CustomEvent('post_batch', {})
                    this.$.infotable.dispatchEvent(event)

                    break;
            }
            if (cleanMsg.player_id == this.playerId) {
                if (cleanMsg.type == 'executed' || cleanMsg.type == 'canceled') {
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
        let states = [marketState, myState]
        this.setProperties
        for (let newState of states) {
            // call this method so property updates are batched 
            this.setProperties(newState)
        }
        this.notifyPath('orderBook._buyOrders')
        let event = new CustomEvent('transaction', {detail: transactions,
            bubbles: true, composed: true})
        this.$.infotable.dispatchEvent(event)
    }

    _handleExternalFeed(message){
        this.eBestBid = message.e_best_bid
        this.eBestOffer = message.e_best_offer
        this.eSignedVolume = message.e_signed_volume;
    }

    _handleMiddlePeg(message){
        this.middlePeg = message.price;
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
        this.notifyPath('orderBook._buyOrders')
    }
    
    _handleExecuted(message) {
        if (message.player_id == this.playerId) {
        let cashChange = message.buy_sell_indicator == 'B' ?  - message.execution_price :
            message.execution_price
        this.cash += cashChange
        this.inventory = message.inventory
        }
        let event = new CustomEvent('transaction', {detail: message,
            bubbles: true, composed: true})
        this.dispatchEvent(event)
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

    _handleSliderConfirm(message) {
        if (message.player_id == this.playerId) {
            let new_sliders = new Object()
            new_sliders.a_x = message.a_x
            new_sliders.a_y = message.a_y
            new_sliders.a_z = message.a_z
            this.sliderValues = new_sliders
        }
    }

    _handleSystemEvent(message) {
        if (message.code == 'S') {
            this.isSessionActive = true
            // another bad hack. disables the ui when the session is over
            // and stops speed calculation and shows the session complete box
            window.setTimeout(function() {
                this.isSessionActive = false;
                this.$.session_complete_indicator.style.display = 'initial';
                this.$.stepwise_calculator.stop();
            }.bind(this), this.sessionLengthMS);
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
            console.error(`invalid message type: ${messagePayload.type} in`, messagePayload);
        }
    }

    _calculateCost(speedCost) {
        return speedCost
    }

    _calculateWealth(cash, costStep, referencePrice, inventory) {
        const out = Math.round((cash - costStep + referencePrice * inventory) * 10) / 10
        return out
    }

    _computeMiddlePeg(eBestBid, eBestOffer) {
        if (OTREE_CONSTANTS.auctionFormat != 'IEX'
            || !eBestBid
            || !eBestOffer
            || eBestBid == MIN_BID
            || eBestOffer >= MAX_ASK) {
            return null;
        }
        return (eBestBid + eBestOffer) / 2;
    }

}

customElements.define('elo-market-session', MarketSession)