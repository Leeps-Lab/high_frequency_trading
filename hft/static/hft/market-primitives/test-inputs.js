import {PolymerElement}  from '../node_modules/@polymer/polymer/polymer-element.js';

class TestInputs extends PolymerElement {

    static get properties() {
        return {
            isRunning: {
                type: Boolean,
                observer: '_runningChanged'
            }
        };
    }

    ready() {
        console.log("Component is ready!");
        if (!TEST_INPUTS_ADDRESS) {
            return;
        }

        const xhr = new XMLHttpRequest();
        xhr.open('GET', TEST_INPUTS_ADDRESS, true);
        xhr.setRequestHeader('cache-control', 'no-cache');
        xhr.onload = () => {
            if (xhr.status != 200) {
                return;
            }
            // parse CSV into array of event objects
            // split into 2d array
            const rows = xhr.response.split('\n')
                .filter(e => e !== '')
                .map(e => e.split(','));
            const header = rows.shift();

            // map array rows to object rows using header for keys
            const eventStrings = rows.map(row => {
                let event = {};
                for (let i = 0; i < header.length; i++) {
                    event[header[i]] = row[i];
                }
                return event;
            });

            // convert types as appropriate
            this._events = eventStrings
                .filter(e => parseInt(e.id) === OTREE_CONSTANTS.idInGroup)
                .map(event => {
                    const type = event['type:value'].split(':')[0];
                    const value = event['type:value'].split(':')[1];
                    return {
                        time: parseInt(event.time),
                        type: type,
                        value: value,
                    }
                });

            // sort by time
            this._events.sort((a, b) => a.time - b.time);
           
            if (this.isRunning && this._startTime) {
                this._start();
                console.log(this._events);
            }
        }
        xhr.send();
    }

    _runningChanged(isRunning) {
        if (isRunning) {
            this._startTime = performance.now();
            this._start();
        }
    }

    _start() {
        if (!this._events) {
            return;
        }
        
        this._curIndex = 0;
        const delay = this._startTime + this._events[this._curIndex].time - performance.now();
        window.setTimeout(this._tick.bind(this), delay);
    }

    _tick() {
        const curEvent = this._events[this._curIndex];
        console.log(curEvent);

        let message = null;
        switch(curEvent.type) {
            case 'role':
                message = {
                    type: 'role_change',
                    state: curEvent.value,
                };
                break;
            case 'speed':
                message = {
                    type: 'speed_change',
                    value: (curEvent.value === 'TRUE'),
                }
                break;
            case 'bid':
                message = {
                    type: 'order_entered',
                    price: parseInt(curEvent.value),
                    buy_sell_indicator: 'B',
                }
                break;
            case 'ask':
                message = {
                    type: 'order_entered',
                    price: parseInt(curEvent.value),
                    buy_sell_indicator: 'S',
                }
                break;
            case 'slider':
                message = {
                    type: 'slider',
                    a_x: parseFloat(curEvent.value.split('-')[0]),
                    a_y: parseFloat(curEvent.value.split('-')[1]),
                    a_z: parseFloat(curEvent.value.split('-')[2]),
                }
        }

        if (message) {
            this.dispatchEvent(new CustomEvent('user-input', {
                bubbles: true,
                composed: true,
                detail: message,
            }));
        }

        this._curIndex++;
        if (this._curIndex >= this._events.length) {
            return;
        }

        const delay = this._startTime + this._events[this._curIndex].time - performance.now();
        window.setTimeout(this._tick.bind(this), delay);
    }

}

window.customElements.define('test-inputs', TestInputs);