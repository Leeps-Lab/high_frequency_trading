
import { PolymerElement, html } from './node_modules/@polymer/polymer/polymer-element.js';
import {PlayersOrderBook} from './market_elements.js'
import './player-strategy/state-selection.js'
import './spread-graph/spread-graph-new.js'
// import './profit-graph/profit-graph-new.js';

const MIN_BID = 0;
const MAX_ASK = 2147483647;



class MarketSession extends PolymerElement {

    static get template() {
        return html`
        <style>
            :host{
                width:100vw;
                height:100vh;
            }

            .middle-section-container{
                display: flex;
                flex-direction: row;
                justify-content: flex-start;
                align-items: center;
                font-weight: bold;
                height: 27vh;
                width: 100vw; 
                background: #4F759B;
                border-top: 3px solid #ED6A5A;
                border-bottom: 3px solid #ED6A5A;
            }

            info-table {
                width: 60%;
                height: 100%;
            }

            state-selection {
                width: 40%;
                height: 100%;
            }

            spread-graph {
                width: 100%;
                height: 200px;
            }

        </style>
            <ws-connection id="websocket" url-to-connect={{websocketUrl}}> </ws-connection>
            <spread-graph orders={{orderBook}}> </spread-graph>
            <div class = "middle-section-container">       
                <info-table  inventory={{inventory}}
                    cash={{cash}} order-imbalance={{orderImbalance}}
                    endowment={{endowment}} best-bid={{bestBid}}
                    best-offer={{bestOffer}} my-bid={{myBid}} my-offer={{myOffer}}> 
                </info-table>

                <state-selection role={{role}} slider-defaults={{sliderDefaults}}> 
                </state-selection>
            </div>
    `;
    }
    static get properties() {
      return {
        eventListeners: Object,
        eventHandlers: Object,
        sliderDefaults: Object,
        events: Object,
        playerId: Number,
        role: String,
        startRole: String,
        orderImbalance: {type: Number,
            value: 0},
        orderBook: Object,
        bestBid: Number,
        volumeBestBid: Number,
        bestOffer: Number,
        volumeBestOffer: Number,
        myBid: Number,
        myOffer: Number,
        inventory: {type: Number,
            value: 0},
        cash: Number,
        endowment: Number,
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

        this.addEventListener('user-input', this.outboundMessage.bind(this))
        this.addEventListener('inbound-ws-message', this.inboundMessage.bind(this))
        
    }

    ready(){
        super.ready();
        this.playerId = OTREE_CONSTANTS.playerId
        this.inventory = 0
        this.orderImbalance = 0
    }

    outboundMessage(event) {
        const messagePayload = event.detail
        let cleanMessage = this._msgSanitize(messagePayload, 'outbound')
        let wsMessage = new CustomEvent('ws-message', {bubbles: true, composed: true, 
            detail: messagePayload })
        this.$.websocket.dispatchEvent(wsMessage)
    }
    
    inboundMessage(event) {
        const messagePayload = event.detail
        let cleanMessage = this._msgSanitize(messagePayload, 'inbound')
        const messageType = cleanMessage.type
        const handlers = this.eventHandlers[messageType]
        for (let i = 0; i < handlers.length; i++) {
            let handlerName = handlers[i]
            this[handlerName](cleanMessage)
        }
    }
    
    _handleExchangeMessage(message) {
        this.orderBook.recv(message)
        if (message.player_id == this.playerId) {
            let mode = message.type == 'executed' || message.type == 'canceled' ?
                'remove' : 'add'
            this._myBidOfferUpdate(message.price, message.buy_sell_indicator, mode=mode)
        }
    }
    
    _handleExecuted(message) {
        this.cash = message.endowment
        this.inventory = message.inventory
    }
    
    _handleBestBidOfferUpdate(message) {
        this.bestBid = message.best_bid
        this.bestOffer = message.best_offer
        this.volumeBestBid = message.volume_bid
        this.volumeBestOffer = message.volume_offer
    }

    _handleRoleConfirm(message) {
        this.role = message.role_name
    }

    _handleSystemEvent(message){

    }

    _handleOrderImbalance(message){
        this.orderImbalance = message.value
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

    _inventoryValueChange(inventory, cash, bestBid, bestOffer) {
        let result = null;
        if (inventory <= 0 && bestOffer != MAX_ASK) {
            result = inventory * bestOffer
        } else if (inventory > 0 && bestBid) {
            result = inventory * bestBid
        }
        return result
    }

    _msgSanitize (messagePayload, direction) {
        if (this.events[direction].hasOwnProperty(messagePayload.type)) {

            let cleanMessage = {}
            let fieldsTypes = this.events[direction][messagePayload.type]
            for (let key in fieldsTypes) {
                let fieldParser = fieldsTypes[key]
                if (!messagePayload.hasOwnProperty(key)) {
                    console.error(`error: ${key} missing in ${messagePayload}`)
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
            console.error(`invalid message type: ${messagePayload.type} in ${messagePayload}`);
        }
    }

}

customElements.define('market-session', MarketSession)

