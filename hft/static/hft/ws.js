import { PolymerElement, html } from './node_modules/@polymer/polymer/polymer-element.js';


var socket = null

class WSConnection extends PolymerElement {
    static get properties() {
      return {
        socket: Object,
        pending: Array,
        urlToConnect: String
      }
    }
    constructor() {
        super();
        this.socket = null;
        this.pendingMessages = [];
    }
    
    ready() {
        if (this.socket) {
            return ;
        }
    
        socket = new WebSocket(this.urlToConnect);

        socket.onerror = this._onError.bind(this);
        socket.onopen = this._onOpen.bind(this);
        socket.onmessage = this._onMessage.bind(this);
        socket.onclose = this._onClose.bind(this);
        this.socket = socket
        this.addEventListener('ws-message', this.send.bind(this))
    }

    _onOpen() {
        console.log('connected to ', this.urlToConnect)
        this.socket = socket
        if (this.pendingMessages.length) {
            this.pendingMessages.forEach( (message) => {
                this.send(message)
                });
        }

        let playerReadyMessage = {
            type: 'player_ready',
        };

        let playerReady = new CustomEvent('user-input', {bubbles: true, composed: true, 
            detail: playerReadyMessage });
        
        this.dispatchEvent(playerReady);
    }

    _onMessage(message) {
        this.socket = socket
        let payload = JSON.parse(message.data);
        if (payload) {
            payload['client_received_timestamp'] = Date.now();
            let event = new CustomEvent('inbound-ws-message', {detail: payload,
                bubbles: true, composed: true});
            this.dispatchEvent(event)
            console.log('websocket received: ', payload, 'and dispatched event: ', event)
        } else { 
            console.log(`error: ${message}`);
        }
    };

    _onError(error) {
        this.socket = socket
        console.error(error);
    };

    _onClose() {
        this.socket = socket
        console.log('disconnected from: ', this.urlToConnect)
        this.socket = null;
    };

    send(event) {
        this.socket = socket
        let message = event.detail
        const jsonMessage = JSON.stringify(message);
        if (this.socket.readyState != 1) {
            this.pending.push(jsonMessage);
            return;
        }
        this.socket.send(jsonMessage);
    }

    static get template() {return html``;}

}

customElements.define('ws-connection', WSConnection)
