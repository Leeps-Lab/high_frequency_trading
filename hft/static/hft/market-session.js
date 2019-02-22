
import { PolymerElement, html } from './node_modules/@polymer/polymer/polymer-element.js';
import {PlayersOrderBook} from './market_elements.js'
import './player-strategy/state-selection.js';
import './profit-graph/profit-graph-new.js';

const MIN_BID = 0;
const MAX_ASK = 2147483647;



class MarketSession extends PolymerElement {
    static get properties() {
      return {
        eventListeners: Object,
        eventHandlers: Object,
        sliderDefaults: Object,
        events: Object,
        active: {type: Boolean, observer: '_activateSession'},
        role: String,
        roles: Object,
        startRole: String,
        orderBook: Object,
        bestBid: Number,
        volumeBestBid: Number,
        bestOffer: Number,
        volumeBestOffer: Number,
        myBid: Number,
        myOffer: Number,
        inventory: Number,
        cash: Number,
        playerId: Number,
        constants: Object,
        endowment: {
            type: Number, 
            computed: '_inventoryValueChange(inventory, cash, bestBid, bestOffer)'
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
        this.playerId = 7
        this.orderBook = new PlayersOrderBook(this.playerId);

        this.addEventListener('user-input', this.outboundMessage.bind(this))
        this.addEventListener('inbound-ws-message', this.inboundMessage.bind(this))

        setTimeout(this._activateSession.bind(this), 3000);
    }

    ready(){
        super.ready();
        for(let role in this.roles){
            if(this.roles[role] == 'selected'){
                this.role = role;
                break;
            }
        }
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
        console.log('message received: ', messagePayload)
        let cleanMessage = this._msgSanitize(messagePayload, 'inbound')
        console.log('cleaned message: ', cleanMessage)
        const messageType = cleanMessage.type
        const handlers = this.eventHandlers[messageType]
        console.log('handler for message: ', handlers)
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

    _activateSession(){  
        this.$.overlay.classList = 'on';
    }

    static get template() {
        return html`
        <!--- 
        To modularize I have to look into ELO.html,
        but will manually style for now - Patrick 2/11 
        --->
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

            #info-table {
                width: 60%;
                height: 100%;
            }

            #input-section {
                width: 40%;
                height: 100%;
            }
            .on{
                opacitiy:1.0;
                pointer-events:all;
            }
            .off{
                opacitiy:0.3;
                pointer-events:none;
            }
        </style>

        <div id = 'overlay' class = 'off'>
            <ws-connection id="websocket" url-to-connect={{websocketUrl}}> </ws-connection>
            <div class = "middle-section-container">       
                <info-table id="info-table" inventory="{{inventory}}" cash={{cash}}
                    endowment={{endowment}} 
                    best-bid={{bestBid}}
                    best-offer={{bestOffer}} my-bid={{myBid}}
                    my-offer={{myOffer}}> 
                </info-table>

                <state-selection 
                id="input-section"
                strategy = {{role}}
                roles = {{roles}}
                slider-defaults = {{sliderDefaults}}
                > 
                </state-selection>
            </div>
        </div>
        
        <!--- 
        To modularize I have to look into ELO.html,
        but will manually put html for now - Patrick 2/11 
        --->
    `;
    }

}

customElements.define('market-session', MarketSession)

