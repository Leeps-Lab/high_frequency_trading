import {PlayersOrderBook} from './market_elements';

const orderBookTest = () => {
    let testBook = new PlayersOrderBook();
    let testMessages = [
        {type: 'confirmed', price: 100, order_token: 'SUBB0001000001', 
            buy_sell_indicator: 'B'},
        {type: 'confirmed', price: 110, order_token: 'SUBS0001000001', 
            buy_sell_indicator: 'S'},
        {type: 'confirmed', price: 103, order_token: 'SUBB0002000001', 
            buy_sell_indicator: 'B'},
        {type: 'replaced', price: 95, old_price: 100, order_token: 'SUBB0001000005', 
            buy_sell_indicator: 'B', old_token: 'SUBB0001000001'},
        {type: 'executed', price: 110, order_token: 'SUBS0001000001', 
            buy_sell_indicator: 'S'},
        {type: 'executed', price: 95, order_token: 'SUBB0001000005', 
            buy_sell_indicator: 'B'},
        {type: 'bbo', best_bid: 0, best_offer: 100, volume_bid: 10, volume_offer: 5},
        {type: 'bbo', best_bid: 5, best_offer: 12, volume_bid: 9, volume_offer: 3}
    ];

    for (let i = 0; i < testMessages.length; i++) {
        testBook.recv(testMessages[i]);
        console.log('buys', JSON.stringify(testBook.getOrders('B')));
        console.log('sells', JSON.stringify(testBook.getOrders('S')));
        console.log('bbo', JSON.stringify(testBook.bbo));
    }

    return testBook;
}

orderBookTest();