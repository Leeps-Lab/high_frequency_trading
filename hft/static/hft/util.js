
const nasdaqMultiplier = 1e4
const MIN_BID = 0
const MAX_ASK = 2147483647

const scaleMultiplierValue = {'price': nasdaqMultiplier, 'execution_price': nasdaqMultiplier, 
    'old_price': nasdaqMultiplier, 'reference_price': nasdaqMultiplier, 
    'cash': nasdaqMultiplier, 'best_bid': nasdaqMultiplier, 
    'best_offer': nasdaqMultiplier, 'bid': nasdaqMultiplier, 'offer': nasdaqMultiplier, 
    'next_bid': nasdaqMultiplier, 'next_offer': nasdaqMultiplier, 'e_best_bid': nasdaqMultiplier,
    'e_best_offer': nasdaqMultiplier}

// functions to transform field values 
// in incoming messages
const scaler = (message, direction) => { 
    let cleanMessage = message
    for (let key in message) {
        let multipler = scaleMultiplierValue[key]
        if (multipler !== undefined) {
            let scaled = message[key]
            try {
                if (scaled == MIN_BID || scaled == MAX_ASK) {
                    continue
                }
                if (direction == 1) {
                    scaled = parseInt(scaled * multipler)
                } else if (direction == 2) {
                    scaled = parseInt(scaled / multipler)
                } else {
                    throw 'invalid direction'
                }
            }
            catch(err) {
                console.error(err)
                continue
            }
            cleanMessage[key] = scaled
        }
    }
    return cleanMessage
}

export {scaler}