import {PolymerElement}  from '../node_modules/@polymer/polymer/polymer-element.js';

function emptyOrUndefined(input) {
    return typeof input === 'undefined' || input === '';
}

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
        const xhr = new XMLHttpRequest();
        xhr.open('GET', '/static/hft/test_input_files/inputs.csv', true);
        xhr.setRequestHeader('cache-control', 'no-cache');
        xhr.onload = () => {
            // parse CSV into array of event objects
            // split into 2d array
            const rows = xhr.response.split('\n')
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
            this._events = eventStrings.map(event => {
                return {
                    time: parseInt(event.time),
                    role: emptyOrUndefined(event.role) ? null : event.role,
                    speed: emptyOrUndefined(event.speed) ? null : (event.speed == 'TRUE'),
                    bid: emptyOrUndefined(event.bid) ? null : parseFloat(event.bid),
                    ask: emptyOrUndefined(event.ask) ? null : parseFloat(event.ask),
                    slider: emptyOrUndefined(event.imbalance_sensitivity) ||
                            emptyOrUndefined(event.inventory_sensitivity)
                            ? null
                            : {
                                a_x: parseFloat(event.imbalance_sensitivity),
                                a_y: parseFloat(event.inventory_sensitivity),
                              },
                };
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

        for (let field in curEvent) {
            const value = curEvent[field];
            if (value === null) {
                continue;
            }

            let message;
            switch(field) {
                case 'role':
                    message = {
                        type: 'role_change',
                        state: value,
                    };
                    break;
                case 'speed':
                    message = {
                        type: 'speed_change',
                        value: value,
                    }
                    break;
                case 'bid':
                    message = {
                        type: 'order_entered',
                        price: value,
                        buy_sell_indicator: 'B',
                    }
                    break;
                case 'ask':
                    message = {
                        type: 'order_entered',
                        price: value,
                        buy_sell_indicator: 'S',
                    }
                    break;
                case 'slider':
                    message = {
                        type: 'slider',
                        a_x: value.a_x,
                        a_y: value.a_y,
                    }
                default:
                    continue;
            }

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