import { PolymerElement, html } from './node_modules/@polymer/polymer/polymer-element.js';

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
    
        let socket = new ReconnectingWebSocket(this.urlToConnect, null, {
            timeoutInterval: 10000
        });

        socket.onerror = this._onError.bind(this);
        socket.onopen = this._onOpen.bind(this);
        socket.onmessage = this._onMessage.bind(this);
        socket.onclose = this._onClose.bind(this);
        this.socket = socket
    }

    _onOpen() {
        if (this.pendingMessages.length) {
            this.pendingMessages.forEach( (message) => {
                this.send(message)
                });
        }
    }

    _onMessage(message) {
        const payload = JSON.parse(message.data);
        cleanMessage = this._inboundMsgSanitize(payload, 'inbound');
        if (cleanMessage) {
            cleanMessage['client_received_timestamp'] = Date.now();
            this.dispatchEvent(new CustomEvent('inbound-ws-message', {message: cleanMessage,
                bubbles: true, composable: true}));
        } else { 
            console.log(`error: ${message}`);
        }
    };

    _onError(error) {
        console.error(error);
    };

    _onClose() {
        this.socket = null;
    };

    send(message) {
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
