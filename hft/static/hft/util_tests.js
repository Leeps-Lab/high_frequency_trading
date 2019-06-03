import {scaler} from './util/scaler.js'

const testMessage = {
    type: 'bbo', best_bid: 10000000, best_offer: 20000000, e_best_bid: 30000000,
    cash: 4000000
} 

const testMessageTwo = {
    type: 'bbo', e_best_offer: 2147483647, best_offer: 0, e_best_bid: 30000000,
    cash: 4000000
}

const test = () => {
    cleanMessage = scaler(testMessage, 1)
    console.log('cleaned message:', cleanMessage)
    cleanMessage = scaler('cleaned message: ', testMessageTwo, 2)
    console.log(cleanMessage)
}
test()