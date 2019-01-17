//     // Handle any errors that occur.
socketActions.socket.onerror = function (error) {
    console.log('WebSocket Error: ' + error);
};

// Show a connected message when the WebSocket is opened.
socketActions.socket.onopen = function (event) {
    console.log('Client has connected to django channels');
    // Also Check if all files exist on the server
};

/*
* Handle messages sent by the server.
*/
var msgCounter = 0;
socketActions.socket.onmessage = function (event) {

    var obj = JSON.parse(event.data);
    msgCounter++;
    console.log("----------");
    console.log("Recieved Message " + msgCounter);
    console.log(obj);

    if(obj["type"] == "bbo"){
        
        if(obj["market_id"]  === otree.marketID){
            otree.handleBBOChange(obj);
        }
        //BBO Change thinking I will call NBBO Change and Shift animation
 
    } else if(obj["type"] == "confirmed"){
        otree.handleConfirm(obj);
    } else if(obj["type"] == "replaced"){
       
        var cancelMessage = {};
        cancelMessage["order_token"] = obj["old_token"];
        cancelMessage["price"] = obj["old_price"];
        cancelMessage["player_id"] = obj["player_id"];
        otree.handleCancel(cancelMessage);
        otree.handleConfirm(obj);
    } else if(obj.type == "canceled"){
        otree.handleCancel(obj);
    } else if(obj.type == "executed"){
        // console.log("EXECUTED");
        otree.handleExecution(obj);
      

        //Do animation
        //Remove executed order on the spread graph

    } else if(obj.type == "system_event"){
        console.log("System Event Message");
        if(obj.code == "S"){
            console.log("Recieved SYNC Message");
            otree.sync = true; 
            otree.startExperiment();
        }
        //Not too sure about this one
    } 
};

// Show a disconnected message when the WebSocket is closed.
socketActions.socket.onclose = function (event) {
    console.log('disconnected from oTree');
};   

otree.handleConfirm = function (obj){
    // console.log("Confirmed order FUNCTION " + obj["order_token"]);
    spreadGraph.addToActiveOrders(obj); 
    
    if(obj["player_id"] == otree.playerID){
        spreadGraph.updateUserBidAndAsk(obj["price"], obj["order_token"][4]);
        if(playersInMarket[otree.playerID]["strategy"] === "maker_basic"){
            if(obj["price"] == spreadGraph.bidArrow["price"]){
                spreadGraph.confirmArrow(obj);
            } else if(obj["price"] == spreadGraph.askArrow["price"]){
                spreadGraph.confirmArrow(obj);
            }
        } else {
            //algorithm player order
            if(obj["order_token"][4] == "B"){
                spreadGraph.drawBidArrow(obj);
            } else if(obj["order_token"][4] == "S"){
                spreadGraph.drawOfferArrow(obj);
            }
        }
        
    }
}

otree.handleCancel = function (obj){
    // console.log("Cancel order " + obj["order_token"]);                
    spreadGraph.removeFromActiveOrders(obj["order_token"],obj["price"]);

    try{
       if(obj["player_id"] == otree.playerID){
           console.log("Removing Arrow");
        spreadGraph.removeArrows(obj["player_token"][4])
       } else {
        console.log("Removing Order Circle");
        spreadGraph.removeOrder(obj["order_token"]);
       }
    } catch {
        console.error("No Order to Cancel with token" + obj["order_token"]);
    }
}

otree.handleExecution = function (obj){
    console.log("Execution Message");
    console.log(obj);
    profitGraph.addProfitJump(obj);
    spreadGraph.removeFromActiveOrders(obj["order_token"],obj["price"]);
    if(obj["player_id"] == otree.playerID){
        //if yes 
        spreadGraph.executeArrow(obj);
    } else {
        spreadGraph.executeOrder(obj);
        //if no
       // spreadGraph.executeOrder(obj);
    }

}

otree.handleBBOChange = function (obj){
    spreadGraph.updateBidAndAsk(obj["best_bid"],obj["best_offer"]);
    spreadGraph.bestBid = obj["best_bid"];
    spreadGraph.bestOffer = obj["best_offer"];
    var shiftNecessary = false;
    // console.log("Changing bid to --> " + obj["best_bid"]);
    // console.log("Changing offer to --> " + obj["best_offer"]);


    // if(obj["best_bid"] > spreadGraph.lowerBound && obj["best_bid"] <  spreadGraph.upperBound){
        
    // } else {
    //     // spreadGraph.spread_svg.select(".best-bid").remove();
    //     shiftNecessary = true;
    // }
    // if(obj["best_offer"] > spreadGraph.lowerBound && obj["best_offer"] <  spreadGraph.upperBound){
        
    // } else {
    //     // spreadGraph.spread_svg.select(".best-offer").remove();
    //     shiftNecessary = true;
    // }
    console.log("Handler Recieved BBO");
    spreadGraph.drawBestBid(obj);
    spreadGraph.drawBestOffer(obj);
    // if(shiftNecessary){
    //     console.log("SHIFT IS NECESSARY--> bid = " + obj["best_bid"] + obj["best_offer"]);
    // } else {
    //     spreadGraph.BBOShift(obj);
    // }
    spreadGraph.BBOShift(obj);
}

otree.playerReady = function (){
    var msg = {
        type: 'player_ready',
    };
    console.log("Sending Player Ready");
    if (socketActions.socket.readyState === socketActions.socket.OPEN) {
        socketActions.socket.send(JSON.stringify(msg));
    }
}

otree.testMessageHandler = function (msg){
    console.log("Recieved test message");
    var obj = msg;
    console.log(obj);

    if(obj.bbo != undefined){
        console.log("---- BEGIN BBO MESSAGE ----");
        if(obj.bbo.type === otree.marketID){
            console.log("Changing bid to --> " + obj.bbo.best_bid);
            console.log("Changing offer to --> " + obj.bbo.best_offer);
            spreadGraph.NBBOChange(obj.bbo.best_bid, obj.bbo.best_offer);
        }
        //BBO Change thinking I will call NBBO Change and Shift animation
        console.log("---- END BBO MESSAGE");
    } else if(obj.confirmed != undefined){
        spreadGraph.addToActiveOrders(obj.confirmed.order_token,obj.confirmed.price);


        console.log("Confirmed order " + obj.confirmed.order_token);
        // if(obj.trader.player_id == otree.player_id){
        //     console.log("Confirmed Current Browser " + obj.trader.player_id);
        //     console.log("Draw Arrows");  
        // }
        // if(obj.confirmed.player_id === otree.player_id){
            //draw arrow
        // } else {
            spreadGraph.drawOrder(obj.confirmed.price, obj.confirmed.order_token);
        // }
    } else if(obj.replaced != undefined){
        // console.log(old order token replaced with new one);
        spreadGraph.removeFromActiveOrders(obj.replaced.replaced_token,obj.replaced.price);
        try{
            spreadGraph.removeOrder(obj.replaced.replaced_token);
        } catch {
            console.log("No Order to replace with token " + obj.replaced.replaced_token);
        }
        spreadGraph.addToActiveOrders(obj.replaced.order_token,obj.replaced.price);

        spreadGraph.drawOrder(obj.replaced.price, obj.replaced.order_token);
    } else if(obj.canceled != undefined){
        console.log("Cancel order " + obj.canceled.order_token);                
        spreadGraph.removeFromActiveOrders(obj.canceled.order_token,obj.canceled.price);

        try{
            spreadGraph.removeOrder(obj.canceled.order_token);
        } catch {
            console.log("No Order to Cancel with token" + obj.canceled.order_token);
        }
    } else if(obj.executed != undefined){
        //Do animation
        //Remove executed order on the spread graph

    } else if(obj.system_event != undefined){
        console.log("System Event Message");
        //Not too sure about this one
        

    } 
}