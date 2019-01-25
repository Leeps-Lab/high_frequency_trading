import {html,PolymerElement}   from '../node_modules/@polymer/polymer/polymer-element.js';

/**
 * @customElement
 * @polymer
 */
class SpreadGraph extends PolymerElement {
  constructor() {
    super();

    //First we access the shadow dom object were working with
    interactiveComponent.spreadGraphDOM = interactiveComponent.interactiveComponentShadowDOM.querySelector("spread-graph");
    interactiveComponent.spreadGraphDOM.attachShadow({mode: 'open'});

    spreadGraph.spread_width = document.querySelector(".front_end_controller").clientWidth;
    spreadGraph.spread_height = document.querySelector(".front_end_controller").clientHeight*0.2;

    spreadGraph.spreadGraphShadowDOM = interactiveComponent.spreadGraphDOM.shadowRoot;
    //Second we add the HTML neccessary to be manipulated in the constructor and the subsequent functions
    spreadGraph.spreadGraphShadowDOM.innerHTML = `
<style>
    .my-batch-flash {
        stroke: BlueViolet;
        stroke-width: 5;
        fill-opacity: 0;
        fill: pink;
    }
    #spread-graph{
        background-color:white;
    }
    .line {
        stroke: steelblue;
        stroke-width: 3.5px;
        fill: none;
    }
    .price-grid-line-text {
        fill: rgb(150, 150, 150);
        font-size: 10px;
        -webkit-user-select: none;
        cursor: default;
    }
    g{
        color:  grey;
        stroke-width: 2px;
        fill: none;

    }
    .my_line{
    stroke:steelblue;
    stroke-width:2px;
    }
    .my_line_attempt{
        stroke:steelblue;
        stroke-width:2px;
        }
    .possible-spread-ticks{
        stroke: grey;
        stroke-width: 1;
    }
    .unconfirmed-order{
        fill: rgb(150, 150, 150);
        stroke:rgb(150, 150, 150);
    }
    .confirmed-bid{
        fill: #309930;
        stroke:#309930;

    }
    .arrow-text{
        font-size: 10px;
    }
    .confirmed-ask{
        fill: rgb(150, 150, 150);
        stroke:rgb(150, 150, 150);

    }
    .others_line{
    stroke:lightgrey;
    stroke-width:2px;
    }

    .green_bar{
    fill:#6edd68;
    opacity: 0.5;
    }

    .blue_bar{
    fill:#00ffff;
    opacity: 0.5;
    }

    .transaction_bar_light{
    fill:#00cc00;
    opacity: 1.0;
    }

    .transaction_bar_light_green{
    fill:#00cc00;
    opacity: 1.0;
    }

    .transaction_bar_light_red{
    fill:#cc0000;
    opacity: 1.0;
    }

    .transaction_bar_dark_green{
    fill:#002900;
    opacity: 0.5;
    }

    .transaction_bar_dark_red{
    fill:#290000;
    opacity: 0.5;
    }
    .best-bid{
        fill:#309930;
    }
    .best-offer{
        fill: #13AAF5;
    }

</style>

<svg id="spread-graph">
<defs>
<marker
  id="bidArrow"
  markerUnits="strokeWidth"
  markerWidth="6"
  markerHeight="6"
  viewBox="0 0 12 12"
  refX="6"
  refY="6"
  orient="auto">
  <path d="M2,2 L10,6 L2,10 L2,2 L2,2" style="fill:rgb(150,150,150);"></path>
</marker>
<marker
  id="askArrow"
  markerUnits="strokeWidth"
  markerWidth="6"
  markerHeight="6"
  viewBox="0 0 12 12"
  refX="6"
  refY="6"
  orient="auto">
  <path d="M2,2 L10,6 L2,10 L2,2 L2,2" style="fill:rgb(150,150,150);"></path>
</marker>
</defs>
</svg>

`;
// <svg id="timer"></svg>
  /*  Spread Constant Information 
     *   otree.maxSpread = {{Constants.max_spread}}; 
     *   otree.defaultSpread = {{Constants.default_spread}};
     *   otree.smallestSpread = {{Constants.smallest_spread}};

     *   Initialize all the values needed for the spread graph and draw the start state
  */
     
    // spreadGraph.spread_width and spreadGraph.spread_height
    // this.spread_width  = Graph_Features.spread_width;
    // this.spread_height = Graph_Features.spread_height;

    //Getting the Shadow DOM variable to be able to use to be selected by d3
    spreadGraph.spread_svg_dom = spreadGraph.spreadGraphShadowDOM.querySelector("#spread-graph");
    spreadGraph.timer_svg_dom = spreadGraph.spreadGraphShadowDOM.querySelector("#timer");
    spreadGraph.spread_svg_dom.style.width = spreadGraph.spread_width;
    spreadGraph.spread_svg_dom.style.height = spreadGraph.spread_height;
    spreadGraph.smallest_spread = true;



    //d3 Selection of the SVG we will be using this variable from now on
    spreadGraph.spread_svg = d3.select(spreadGraph.spread_svg_dom);
    spreadGraph.timer_svg = d3.select(spreadGraph.timer_svg_dom);

    /*
      Functions attached to the spreadGraph object
    */

    spreadGraph.start = this.start;
    spreadGraph.dis = true;
    //Onclick listener . . .  of course
    spreadGraph.listen = this.listen;
    spreadGraph.sendSpreadChange = this.sendSpreadChange;
    spreadGraph.drawMySpreadLines = this.drawMySpreadLines;
    spreadGraph.clear = this.clear;
    spreadGraph.addOthersLineAnimation = this.addOthersLineAnimation;
    spreadGraph.drawTransactionBar = this.drawTransactionBar;    
    spreadGraph.drawSpreadBar = this.drawSpreadBar;
    
    spreadGraph.drawBatchFlash = this.drawBatchFlash;
    spreadGraph.startBatchTimer = this.startBatchTimer;
    spreadGraph.drawPossibleSpreadTicks = this.drawPossibleSpreadTicks;
    spreadGraph.updateFBASpreadGraphLines = this.updateFBASpreadGraphLines;
    spreadGraph.drawLineAttempt = this.drawLineAttempt;
    spreadGraph.drawFPC = this.drawFPC;
    spreadGraph.executionHandler = this.executionHandler;
    spreadGraph.drawSpreadChange = this.drawSpreadChange;


    spreadGraph.drawArrows = this.drawArrows;
    spreadGraph.removeArrows = this.removeArrows;
    spreadGraph.confirmArrow = this.confirmArrow;
    spreadGraph.drawOfferArrow = this.drawOfferArrow;
    spreadGraph.drawBidArrow = this.drawBidArrow;
    spreadGraph.executeArrow = this.executeArrow;


    spreadGraph.NBBOChange = this.NBBOChange;
    spreadGraph.drawBestBid = this.drawBestBid;
    spreadGraph.drawBestOffer = this. drawBestOffer;
    spreadGraph.BBOShift = this.BBOShift;
    spreadGraph.animateBBOShift = this.animateBBOShift;

    spreadGraph.drawOrder = this.drawOrder;
    spreadGraph.removeOrder = this.removeOrder;
    spreadGraph.executeOrder = this.executeOrder;

    spreadGraph.addToActiveOrders = this.addToActiveOrders;
    spreadGraph.removeFromActiveOrders = this.removeFromActiveOrders;
    spreadGraph.replaceActiveOrder = this.replaceActiveOrder;

    spreadGraph.visibleTickLines = {};
    spreadGraph.tickLines = [];
    spreadGraph.tickLinesText = [];
    spreadGraph.orderD3Objects = [];


    spreadGraph.updateBidAndAsk = this.updateBidAndAsk;
    spreadGraph.updateUserBidAndAsk = this.updateUserBidAndAsk;
    /*
        price: price it is pointed at
        d3 arrow line: line created in d3 that maps to yCoordinate to price just above
        textline : text d3 function for "bid" or "ask"
    */
    spreadGraph.bidArrow = {};
    spreadGraph.askArrow = {};

    spreadGraph.numPriceTicks = 20;
    spreadGraph.startingLowerBound = 800000;
    spreadGraph.startingUpperBound = 1000000;
    
    //Creating the start state
    spreadGraph.start();

  }

  start(){
    /*Drawing the start state when the window opens*/
    var priceLine = spreadGraph.spread_svg.append("svg:line")
                       .attr("x1", 0)
                       .attr("y1", spreadGraph.spread_height*0.3)
                       .attr("x2", spreadGraph.spread_width)
                       .attr("y2", spreadGraph.spread_height*0.3)
                       .style("stroke", "lightgrey")
                       .style("stroke-width", 3);

    // Grey Line in the middle of the spread graph
    var topPointerInputLine = spreadGraph.spread_svg.append("svg:line")
                       .attr("x1",0)
                       .attr("y1", spreadGraph.spread_height*0.6)
                       .attr("x2", spreadGraph.spread_width)
                       .attr("y2", spreadGraph.spread_height*0.6)
                       .style("stroke", "grey")
                       .style("stroke-width", 5);

   

    if(otree.FBA == true){
        //Only draw the batch timer if FBA is true
        var batch_timer = spreadGraph.timer_svg.append("svg:line")
                            .attr("x1", 0)
                            .attr("y1", spreadGraph.spread_height - 10)
                            .attr("x2", spreadGraph.spread_width)
                            .attr("y2", spreadGraph.spread_height - 10)
                            .style("stroke", "grey")
                            .style("stroke-width", 3);
    }   

    spreadGraph.drawPossibleSpreadTicks();  
  }


  BBOShift(shiftMsg){
    console.log("BBO!");
    console.log(spreadGraph.visibleTickLines);
    var bestBidCircle = spreadGraph.spread_svg.select(".best-bid");
    var bestOfferCircle = spreadGraph.spread_svg.select(".best-offer");
    var smallerX = (bestBidCircle.attr("cx") <=  bestOfferCircle.attr("cx")) ? bestBidCircle.attr("cx") : bestBidCircle.attr("cx");
    var diff = Math.abs(bestBidCircle.attr("cx") - bestOfferCircle.attr("cx"));
    var desiredCenter = (diff/2) + +smallerX;
    
    //Center is between the best bid and the best offer


    // if((spreadGraph.bestBid != undefined && spreadGraph.bestOffer != undefined) && (spreadGraph.bestBid != 0 || spreadGraph.bestOffer != 0)){
        spreadGraph.animateBBOShift(desiredCenter,shiftMsg);
    // }
    
  } 

  animateBBOShift(desiredCenter, obj){
    var tickArray = Object.keys(spreadGraph.visibleTickLines);
    for(var i = 0; i < tickArray.length; i++){
        // console.log(spreadGraph.visibleTickLines[tickArray[i]]);
        if(spreadGraph.visibleTickLines[tickArray[i]] >= desiredCenter){
            break;
        }
    }
    var newMiddlePrice = tickArray[i];

    var differenceFromMid = Math.abs(spreadGraph.visibleTickLines[newMiddlePrice] - spreadGraph.spread_width/2);

     //Animate All Spread Line Text Values
     spreadGraph.tickLinesText.forEach(text => { 
        text.transition()
            .duration(300)
            .attr("x", ((desiredCenter < spreadGraph.spread_width/2 ) ? +text.attr("x") + differenceFromMid : +text.attr("x") - differenceFromMid))
            .on("end", function() { text.remove()})

    });
     //Animate All Spread Line Text Values
     spreadGraph.tickLines.forEach(line => { 
        
        line.transition()
            .duration(300)
            .attr("x1", ((desiredCenter > spreadGraph.spread_width/2) ? +line.attr("x1") - differenceFromMid : +line.attr("x1") + differenceFromMid))
            .attr("x2", ((desiredCenter > spreadGraph.spread_width/2) ? +line.attr("x2") - differenceFromMid : +line.attr("x2") + differenceFromMid))
            .on("end", function() { line.remove()})
    });
    //Redraw possiible spread ticks with updated best bid and best offer
   
    spreadGraph.drawPossibleSpreadTicks(+newMiddlePrice - 100000, +newMiddlePrice + 100000);
    //Shift Best Bid and Best Offer
    var bestBidCircle = spreadGraph.spread_svg.select(".best-bid");
    var bestOfferCircle = spreadGraph.spread_svg.select(".best-offer");

    bestBidCircle.transition()
                 .duration(300)
                 .attr("cx", ((desiredCenter > spreadGraph.spread_width/2) ? +bestBidCircle.attr("cx") - differenceFromMid : +bestBidCircle.attr("cx") + differenceFromMid))
                 .attr("r", obj["volume_bid"]*4)
     
    bestOfferCircle.transition()
                 .duration(300)
                 .attr("cx", ((desiredCenter > spreadGraph.spread_width/2) ? +bestOfferCircle.attr("cx") - differenceFromMid : +bestOfferCircle.attr("cx") + differenceFromMid))
                 .attr("r", obj["volume_offer"]*4)

    //Shift all orders 

    // Shift Arrow
    

    try{
        console.log("Bid Arrow ANIMATION");
        spreadGraph.bidArrow["bidArrowText"].transition().duration(300).attr("x",(desiredCenter > spreadGraph.spread_width/2) ? +spreadGraph.bidArrow["bidArrowText"].attr("x") - differenceFromMid : +spreadGraph.bidArrow["bidArrowText"].attr("x")  + differenceFromMid);
        spreadGraph.bidArrow["bidArrowLine"].transition().duration(300).attr("x1",(desiredCenter > spreadGraph.spread_width/2) ? +spreadGraph.bidArrow["bidArrowLine"].attr("x1") - differenceFromMid : +spreadGraph.bidArrow["bidArrowLine"].attr("x1")  + differenceFromMid)
                                                                    .attr("x2",(desiredCenter > spreadGraph.spread_width/2) ? +spreadGraph.bidArrow["bidArrowLine"].attr("x2") - differenceFromMid : +spreadGraph.bidArrow["bidArrowLine"].attr("x2")  + differenceFromMid);
    } catch {
        console.log("Bid Arrow not Exist");
    }
    try{
        console.log("Bid Offer ANIMATION");
        spreadGraph.askArrow["askArrowText"].transition().duration(300).attr("x",(desiredCenter > spreadGraph.spread_width/2) ? +spreadGraph.askArrow["askArrowText"].attr("x") - differenceFromMid : +spreadGraph.askArrow["askArrowText"].attr("x")  + differenceFromMid);
        spreadGraph.askArrow["askArrowLine"].transition().duration(300).attr("x1",(desiredCenter > spreadGraph.spread_width/2) ? +spreadGraph.askArrow["askArrowLine"].attr("x1") - differenceFromMid : +spreadGraph.askArrow["askArrowLine"].attr("x1")  + differenceFromMid)
                                                                    .attr("x2",(desiredCenter > spreadGraph.spread_width/2) ? +spreadGraph.askArrow["askArrowLine"].attr("x2") - differenceFromMid : +spreadGraph.askArrow["askArrowLine"].attr("x2")  + differenceFromMid);
    } catch {
        console.log("Ask Arrow not existing");
    }


    for(var price in spreadGraph.activeOrders){

        for(var i = 0; i <  spreadGraph.activeOrders[price].length; i++){
     
            if(spreadGraph.activeOrders[price][i]["selection"] != undefined){
                spreadGraph.activeOrders[price][i]["selection"].transition()
                .duration(300)
                .attr("cx", ((desiredCenter > spreadGraph.spread_width/2) ? +spreadGraph.activeOrders[price][i]["selection"].attr("cx") - differenceFromMid : +spreadGraph.activeOrders[price][i]["selection"].attr("cx") + differenceFromMid))
            }
        }
    }   
   
  }

  drawBestBid(obj){
        spreadGraph.spread_svg.select(".best-bid").remove();
        var bidX = spreadGraph.visibleTickLines[obj["best_bid"]];
        bidX = (bidX == undefined) ? 0 : bidX ;
        if(+obj["best_bid"] < spreadGraph.lowerBound){
            bidX = -5;
        } else if(+obj["best_bid"] > spreadGraph.upperBound){
            bidX = spreadGraph.spread_width + 5;
        }   

        if(bidX == undefined){
            
            var tickArray = Object.keys(spreadGraph.visibleTickLines);
            for(var i = 0; i < tickArray.length; i++){
                if(tickArray[i] > obj["best_bid"]){
                    break;
                }
            }
            var upperPrice = tickArray[i];
            var lowerPrice = tickArray[i-1];
            var priceDiff = upperPrice - lowerPrice;
            var bidDiff = Math.abs(obj["best_bid"] - lowerPrice);
    
            var ratio = bidDiff/priceDiff;
    
            var diffX = +spreadGraph.visibleTickLines[tickArray[i]] - +spreadGraph.visibleTickLines[tickArray[i - 1]];
            var xRatio = diffX*ratio;
            bidX =  +spreadGraph.visibleTickLines[tickArray[i - 1]] + xRatio;
            
    
        }

        spreadGraph.spread_svg.append("circle")
        .attr("cx", bidX)
        .attr("cy", spreadGraph.spread_height*0.3)
        .attr("r", obj["volume_bid"]*4)
        .attr("stroke", "black")
        .attr("class","best-bid");

  }

  drawBestOffer(obj){

        spreadGraph.spread_svg.select(".best-offer").remove();

        var offerX = spreadGraph.visibleTickLines[obj["best_offer"]];

        if(+obj["best_offer"] < spreadGraph.lowerBound){
            offerX = -5;
        } else if(+obj["best_offer"] > spreadGraph.upperBound){
            offerX = spreadGraph.spread_width + 5;
        }   
        
    if(offerX == undefined){
        var tickArray = Object.keys(spreadGraph.visibleTickLines);
        for(var i = 0; i < tickArray.length; i++){
            if(tickArray[i] > obj["best_offer"]){
                break;
            }
        }
        var upperPriceOffer = tickArray[i];
        var lowerPriceOffer = tickArray[i-1];
        var priceDiffOffer = upperPriceOffer - lowerPriceOffer;
        var offerDiff = Math.abs(obj["best_offer"] - lowerPrice);

        var ratioOffer = offerDiff/priceDiffOffer;

        var diffXOffer = +spreadGraph.visibleTickLines[tickArray[i]] - +spreadGraph.visibleTickLines[tickArray[i - 1]];
        var xRatioOffer = diffXOffer*ratioOffer;
        offerX =  +spreadGraph.visibleTickLines[tickArray[i - 1]] + xRatioOffer;
    }

    spreadGraph.spread_svg.append("circle")
        .attr("cx", offerX)
        .attr("cy", spreadGraph.spread_height*0.3)
        .attr("r", obj["volume_offer"]*4)
        .attr("stroke", "black")
        .attr("class","best-offer");

  }

  drawOrder(price, TOK ){
    
    //What do I need from this?
    if(TOK[4] == "B"){
        var orderBid = spreadGraph.spread_svg.append("circle")
            .attr("cx", spreadGraph.visibleTickLines[price])
            .attr("cy", spreadGraph.spread_height*0.3)
            .attr("r", 5)
            .attr("fill","#309930")
            .attr("class","order " + TOK);
        spreadGraph.orderD3Objects.push(orderBid);
        return orderBid;
        
    } else if(TOK[4] == "S"){
        var orderOffer = spreadGraph.spread_svg.append("circle")
            .attr("cx", spreadGraph.visibleTickLines[price])
            .attr("cy", spreadGraph.spread_height*0.3)
            .attr("r", 5)
            .attr("fill","#13AAF5")
            .attr("class","order " + TOK);
        spreadGraph.orderD3Objects.push(orderOffer);
        return orderOffer;
        
    } else{
        console.error("Invalid Order Token " + TOK);
    }

    //draw the order on top of everything 
  }

  removeOrder(TOK){

    // console.log( spreadGraph.orderD3Objects);
    var orderObj = spreadGraph.spread_svg.select("." + TOK);
    // console.log("STILL NEED TO REMOVE ORDER REMOVE MESSAGE WHEN DONE");
    orderObj.remove();
    // for(var i = 0; i < spreadGraph.orderD3Objects.length; i++){
    //     console.log(spreadGraph.orderD3Objects[i]["_groups"][0].classList);
    //     var index = spreadGraph.orderD3Objects[i]["groups"][0].classList.indexOf(TOK);
    //     if(index != -1){
    //         console.log("Removing index " + index);
    //         spreadGraph.orderD3Objects.splice(index,1);
    //     }
    // }
    // console.log(spreadGraph.orderD3Object);
    //Remove from d3 orders as well
  }
  replaceOrder(oldTOK, newTOK, newPrice){
    spreadGraph.removeOrder(oldTOK);
    spreadGraph.drawOrder(newPrice,newTOK);
  }

  drawArrows(){

      //Green Bid --> #309930
      //Red ask --> #CB1C36
    
    var midPrice = (spreadGraph.lowerBound + spreadGraph.upperBound)/2;
    spreadGraph.bidArrow["price"] = midPrice - 10000;
    spreadGraph.askArrow["price"] = midPrice + 10000;

    spreadGraph.bidArrow["bidArrowLine"] = spreadGraph.spread_svg.append("line")
        .attr("x1",spreadGraph.visibleTickLines[spreadGraph.bidArrow["price"]])  
        .attr("y1",spreadGraph.spread_height - 25)  
        .attr("x2",spreadGraph.visibleTickLines[spreadGraph.bidArrow["price"]])  
        .attr("y2",spreadGraph.spread_height*0.6 + 20)  
        .attr("stroke","rgb(150,150,150)") 
        .attr("stroke-width",7)  
        .attr("marker-end","url(#bidArrow)")
        .attr("class", "arrow");
 
        
    spreadGraph.askArrow["askArrowLine"] = spreadGraph.spread_svg.append("line")
        .attr("x1",spreadGraph.visibleTickLines[spreadGraph.askArrow["price"]])  
        .attr("y1",spreadGraph.spread_height - 25)  
        .attr("x2",spreadGraph.visibleTickLines[spreadGraph.askArrow["price"]])  
        .attr("y2",spreadGraph.spread_height*0.6 + 20)  
        .attr("stroke","rgb(150,150,150)") 
        .attr("stroke-width",7)  
        .attr("marker-end","url(#askArrow)")
        .attr("class", "arrow ");
        
    if(playersInMarket[otree.playerID]["strategy"] === "maker_basic"){
        spreadGraph.bidArrow["bidArrowLine"].call(d3.drag()
            .on("drag", function(){
                spreadGraph.bidArrow["bidArrowLine"].attr("stroke", "rgb(150,150,150)");
                spreadGraph.bidArrow["bidArrowText"].attr("fill","rgb(150,150,150)");
                spreadGraph.spreadGraphShadowDOM.querySelector("#bidArrow").querySelector("path").style.fill = "rgb(150,150,150)";
                //Making sure not to drag past other arrow line
                var lineX = (spreadGraph.askArrow["askArrowLine"].attr("x1") - 10 <= d3.event.x) ? spreadGraph.askArrow["askArrowLine"].attr("x1") - 10: d3.event.x ;
                spreadGraph.bidArrow["bidArrowText"].attr("x", lineX - 10);
                spreadGraph.bidArrow["bidArrowLine"].attr("x1",  lineX).attr("x2", lineX);
            })
            .on("end", function(){
                    //finding the price in which is just past the dropped x value
                    var x = +spreadGraph.bidArrow["bidArrowLine"].attr("x1");
                    var tickArray = Object.keys(spreadGraph.visibleTickLines);
                    for(var i = 0; i < tickArray.length; i++){
                        if(spreadGraph.visibleTickLines[tickArray[i]] > x){
                            break;
                        }
                    }
                    //finding diff from upper and lower
                    var diffUpper =  Math.abs(spreadGraph.visibleTickLines[tickArray[i]] - x);
                    var diffLower = Math.abs(spreadGraph.visibleTickLines[tickArray[i - 1]]  - x);
                    
                    // Snapping to the closes price based on drop
                    var snappedX = (diffUpper < diffLower) ? spreadGraph.visibleTickLines[tickArray[i]] : spreadGraph.visibleTickLines[tickArray[i - 1]];
                    var snappedPrice = (diffUpper < diffLower) ? tickArray[i] : tickArray[i - 1];
                    
                    //Check for ask line x making sure it cant snap to other line 
                    var checkedX = (spreadGraph.askArrow["askArrowLine"].attr("x1") == snappedX) ? spreadGraph.visibleTickLines[tickArray[i - 1]] : snappedX;
                    var checkedPrice = (spreadGraph.askArrow["askArrowLine"].attr("x1") == snappedX) ? tickArray[i - 1] : snappedPrice;
                    
                    spreadGraph.bidArrow["price"] = checkedPrice;
                    /*
                        //SEND spreadGraph.bidArrow["bidArrowLine"].price OVER SOCKET ********* 
                    */

                    var bidPriceMessage = {
                        type:  "order_by_arrow",
                        side: "B",
                        price: checkedPrice
                    };
                    if(socketActions.socket.readyState === socketActions.socket.OPEN){
                        console.log(JSON.stringify(bidPriceMessage));
                        socketActions.socket.send(JSON.stringify(bidPriceMessage));
                    }

                    spreadGraph.bidArrow["bidArrowText"].attr("x", checkedX - 10);
                    spreadGraph.bidArrow["bidArrowLine"].attr("x1",  checkedX).attr("x2", checkedX);

                }   
            )
        
        );

        spreadGraph.askArrow["askArrowLine"].call(d3.drag()
            .on("drag", function(){
                spreadGraph.askArrow["askArrowLine"].attr("stroke", "rgb(150,150,150)");
                spreadGraph.askArrow["askArrowText"].attr("fill","rgb(150,150,150)");
                spreadGraph.spreadGraphShadowDOM.querySelector("#askArrow").querySelector("path").style.fill = "rgb(150,150,150)";
                //Making sure not to drag past other arrow line
                var lineXAsk = (+spreadGraph.bidArrow["bidArrowLine"].attr("x1") + 10 >= d3.event.x) ? +spreadGraph.bidArrow["bidArrowLine"].attr("x1") + 10: d3.event.x ;
                spreadGraph.askArrow["askArrowText"].attr("x", lineXAsk - 10);
                spreadGraph.askArrow["askArrowLine"].attr("x1",  lineXAsk).attr("x2", lineXAsk);
            })
            .on("end", function(){
                    //finding the price in which is just past the dropped x value
                    var xAsk = +spreadGraph.askArrow["askArrowLine"].attr("x1");
                    var tickArray = Object.keys(spreadGraph.visibleTickLines);
                    for(var i = 0; i < tickArray.length; i++){
                        if(+spreadGraph.visibleTickLines[tickArray[i]] > xAsk){
                            break;
                        }
                    }
                    //finding diff from upper and lower
                    var diffUpperAsk =  Math.abs(spreadGraph.visibleTickLines[tickArray[i]] - xAsk);
                    var diffLowerAsk = Math.abs(spreadGraph.visibleTickLines[tickArray[i - 1]]  - xAsk);
                    
                    // Snapping to the closes price based on drop
                    var snappedXAsk = (diffUpperAsk < diffLowerAsk) ? spreadGraph.visibleTickLines[tickArray[i]] : spreadGraph.visibleTickLines[tickArray[i - 1]];
                    var snappedPriceAsk = (diffUpperAsk < diffLowerAsk) ? tickArray[i] : tickArray[i - 1];
            
                    //Check for ask line x making sure it cant snap to other line 
                    var checkedXAsk = (+spreadGraph.bidArrow["bidArrowLine"].attr("x1") == snappedXAsk) ? spreadGraph.visibleTickLines[tickArray[i]] : snappedXAsk;
                    var checkedPriceAsk = (+spreadGraph.bidArrow["bidArrowLine"].attr("x1") == snappedXAsk) ? tickArray[i] : snappedPriceAsk;
                    
                    spreadGraph.askArrow["price"] = checkedPriceAsk;
                    var askPriceMessage = {
                        type:  "order_by_arrow",
                        side: "S",
                        price: checkedPriceAsk
                    };
                    if(socketActions.socket.readyState === socketActions.socket.OPEN){
                        console.log(JSON.stringify(askPriceMessage));
                        socketActions.socket.send(JSON.stringify(askPriceMessage));
                    }
                    spreadGraph.askArrow["askArrowText"].attr("x", checkedXAsk - 10);
                    spreadGraph.askArrow["askArrowLine"].attr("x1",  checkedXAsk).attr("x2", checkedXAsk);

                }   
            )
            
        );
    }
        

    spreadGraph.bidArrow["bidArrowText"]  = spreadGraph.spread_svg.append("text")
        .attr("text-anchor", "start")
        .attr("x", +spreadGraph.bidArrow["bidArrowLine"].attr("x1") - 10)  
        .attr("y",  spreadGraph.spread_height - 10)
        .attr("fill","rgb(150,150,150)")
        .attr("class", "arrow-text arrow")
        .text("BID");

    spreadGraph.askArrow["askArrowText"]  = spreadGraph.spread_svg.append("text")
        .attr("text-anchor", "start")
        .attr("x", +spreadGraph.askArrow["askArrowLine"].attr("x1") - 10)  
        .attr("y",  spreadGraph.spread_height - 10)
        .attr("fill","rgb(150,150,150)")
        .attr("class", "arrow-text arrow")
        .text("ASK");        
  }

  confirmArrow(obj){
    //confirm the arrow by drawing differnt strokes on it
    if(obj["order_token"][4] == "B"){
        spreadGraph.bidArrow["token"] = obj["order_token"];
        spreadGraph.bidArrow["bidArrowLine"].attr("stroke", "#309930");
        spreadGraph.bidArrow["bidArrowText"].attr("fill","#309930");
        spreadGraph.spreadGraphShadowDOM.querySelector("#bidArrow").querySelector("path").style.fill = "#309930";
    } else if(obj["order_token"][4] == "S"){
        spreadGraph.askArrow["token"] = obj["order_token"];
        spreadGraph.askArrow["askArrowLine"].attr("stroke", "#13AAF5");
        spreadGraph.askArrow["askArrowText"].attr("fill","#13AAF5");
        spreadGraph.spreadGraphShadowDOM.querySelector("#askArrow").querySelector("path").style.fill = "#13AAF5";
    }
  }

  executeArrow(obj){
      
    //confirm the arrow by drawing differnt strokes on it
    console.log("EXECUTING OFFER ARROW");
    console.log(obj);
    if(obj["order_token"][4] == "B"){
        console.log("EXECUTING BID ARROW");
        spreadGraph.bidArrow["token"] = "";
        spreadGraph.bidArrow["bidArrowLine"].transition()
                                            .duration(100)
                                            .style("opacity", 0.0)
                                            .on("end", function() {spreadGraph.bidArrow["bidArrowLine"].style("opacity", 1.0).attr("stroke", "rgb(150,150,150)") } 
                                            );
        spreadGraph.bidArrow["bidArrowText"].transition()
                                            .duration(100)
                                            .style("opacity", 0.0)
                                            .on("end", function() {spreadGraph.bidArrow["bidArrowText"].style("opacity", 1.0).attr("fill", "rgb(150,150,150)") } 
                                            );

        spreadGraph.spread_svg.select("#bidArrow").transition()
                                                .duration(100)
                                                .style("opacity", 0.0)
                                                .on("end", function() {spreadGraph.spread_svg.select("#bidArrow").style("opacity", 1.0).attr("fill", "rgb(150,150,150)")
                                                spreadGraph.spreadGraphShadowDOM.querySelector("#bidArrow").querySelector("path").style.fill = "rgb(150,150,150)"; } 
                                            );

    } else if(obj["order_token"][4] == "S"){
        console.log("EXECUTING OFFER ARROW");
        spreadGraph.askArrow["token"] = "";
        spreadGraph.askArrow["askArrowLine"].transition()
                                            .duration(100)
                                            .style("opacity", 0.0)
                                            .on("end", function() {spreadGraph.askArrow["askArrowLine"].style("opacity", 1.0).attr("stroke", "rgb(150,150,150)") } 
                                            );
        spreadGraph.askArrow["askArrowText"].transition()
                                            .duration(100)
                                            .style("opacity", 0.0)
                                            .on("end", function() {spreadGraph.askArrow["askArrowText"].style("opacity", 1.0).attr("fill", "rgb(150,150,150)") } 
                                            );

        spreadGraph.spread_svg.select("#askArrow").transition()
                                                .duration(100)
                                                .style("opacity", 0.0)
                                                .on("end", function() {spreadGraph.spread_svg.select("#askArrow").style("opacity", 1.0).attr("fill", "rgb(150,150,150)")
                                                spreadGraph.spreadGraphShadowDOM.querySelector("#askArrow").querySelector("path").style.fill = "rgb(150,150,150)"; } 
                                            );
    }
  }
  executeOrder(obj){
    var orderCircle = spreadGraph.spread_svg.select("." + obj["order_token"]);
    orderCircle.transition().duration(100).attr("fill", "rgb(150,150,150)");
    spreadGraph.removeOrder(obj["order_token"]);

  }

  drawBidArrow(obj){
    console.log("Drawing Bid Arrow");
    console.log(spreadGraph.lowerBound, spreadGraph.upperBound);
    console.log(spreadGraph.visibleTickLines);

    spreadGraph.bidArrow["bidArrowLine"].attr("x1", spreadGraph.visibleTickLines[obj["price"]]).attr("x2", spreadGraph.visibleTickLines[obj["price"]]);
    spreadGraph.bidArrow["bidArrowText"].attr("x", spreadGraph.visibleTickLines[obj["price"]] - 10);
    spreadGraph.confirmArrow(obj);
  }

  drawOfferArrow(obj){
    console.log("Drawing Offer Arrow");
    console.log(spreadGraph.lowerBound, spreadGraph.upperBound);
    console.log(spreadGraph.visibleTickLines);

    spreadGraph.askArrow["askArrowLine"].transition().duration(100).attr("x1", spreadGraph.visibleTickLines[obj["price"]]).attr("x2", spreadGraph.visibleTickLines[obj["price"]]);
    spreadGraph.askArrow["askArrowText"].transition().duration(100).attr("x", spreadGraph.visibleTickLines[obj["price"]] - 10);
    spreadGraph.confirmArrow(obj);


}

  removeArrows(side = ""){

    try {
        if(side == ""){
            spreadGraph.spread_svg.selectAll(".arrow").remove();
        } else if(side == "B"){
            spreadGraph.bidArrow["bidArrowLine"].attr("stroke", "rgb(150,150,150)");
            spreadGraph.bidArrow["bidArrowText"].attr("fill", "rgb(150,150,150)");
        } else if(side == "S"){
            spreadGraph.askArrow["askArrowLine"].attr("stroke", "rgb(150,150,150)");
            spreadGraph.askArrow["askArrowText"].attr("fill", "rgb(150,150,150)");
        }
    } catch {
        console.error("No Arrows to remove");
    }
  }

  
  addToActiveOrders(obj){
    var orderObj = {};
    orderObj["token"] = obj["order_token"];
    orderObj["player_id"] = obj["player_id"];
    
    if(obj["player_id"] != otree.playerID){
        orderObj["selection"] = spreadGraph.drawOrder(obj["price"], obj["order_token"]);
    }

    if(spreadGraph.activeOrders[obj["price"]] != undefined){
        spreadGraph.activeOrders[obj["price"]].push(orderObj);
    } else {
        spreadGraph.activeOrders[obj["price"]] = [] ;
        spreadGraph.activeOrders[obj["price"]].push(orderObj);
    }
    
  }

  removeFromActiveOrders(oldToken, oldPrice){
    if(spreadGraph.activeOrders[oldPrice] != undefined){
        for(var i = 0 ; i < spreadGraph.activeOrders[oldPrice].length; i++){
            var index = -1;
            if(spreadGraph.activeOrders[oldPrice][i]["token"] == oldToken ){
                index = i;
                break;
            }
        }
        if(index != -1){
            spreadGraph.activeOrders[oldPrice].splice(index,1);
        }
    }

  }

  replaceActiveOrder(newToken, newPrice, oldToken, oldPrice){
    spreadGraph.removeFromActiveOrders(oldToken,oldPrice);
    spreadGraph.addToActiveOrders(newToken,newPrice);
  }

   
    /*
    * IEX Specififc Function
    * Draws the possible spread ticks based on the set of possible spread ticks
    */
    drawPossibleSpreadTicks(lowerBound = spreadGraph.startingLowerBound, upperBound = spreadGraph.startingUpperBound){
        
        //Drawn on  shift message maybe inputs include
        spreadGraph.lowerBound = lowerBound;
        spreadGraph.upperBound = upperBound;
        var diff = upperBound - lowerBound;
        var increment  =   10000;
        var incrementNum = diff / increment;
        var distanceBetweenLines = spreadGraph.spread_width/incrementNum;
        var xCoordinate = 0;
        var yCoordinate = spreadGraph.spread_height*0.3;
        spreadGraph.visibleTickLines = {};
        for(var temp = lowerBound; temp <= upperBound; temp+=increment){
            spreadGraph.visibleTickLines[temp] = xCoordinate;
            spreadGraph.tickLines.push(spreadGraph.spread_svg.append("svg:line")
                    .attr("x1", xCoordinate)
                    .attr("y1", spreadGraph.spread_height*0.3 - 15)
                    .attr("x2", xCoordinate)
                    .attr("y2", spreadGraph.spread_height*0.3 + 15)
                    .attr("stroke-width",1)
                    .attr("class","possible-spread-ticks"));  
                
            spreadGraph.tickLinesText.push(spreadGraph.spread_svg.append("text")
                    .attr("text-anchor", "start")
                    .attr("x", xCoordinate - 5)  
                    .attr("y",  spreadGraph.spread_height*0.6 - 10)
                    .attr("class", "price-grid-line-text")
                    .text((temp/10000).toFixed(0)));

                xCoordinate += distanceBetweenLines;                
        }
    }

    /*
    * IEX Specific 
    */
    drawQueue(){
        var userPlayerID = otree.playerIDInGroup;
        var index = -1;
        var xOffset = 0;
    
        for(var price in spreadGraph.queue){
            index = parseInt(spreadGraph.queue[price].indexOf(userPlayerID.toString()));
            if(index != -1){
                for(var user = 0; user <= spreadGraph.queue[price].length - 1; user++){
                    var svgMiddleY = spreadGraph.spread_height/2;
                    var mySpread = price;
                    var moneyRatio =  otree.maxSpread/mySpread;
                    var yCoordinate = svgMiddleY/moneyRatio;
                    if(spreadGraph.queue[price][user] == userPlayerID){
                        spreadGraph.spread_svg.select(".user-bubble").remove();
                        spreadGraph.spread_svg.append("circle")
                            .attr("cx", (spreadGraph.spread_width / 2) + 35 + xOffset)
                            .attr("cy", svgMiddleY - yCoordinate)
                            .attr("r", 5)
                            .attr("class","queue user-bubble");
                    } else {
                        spreadGraph.spread_svg.select(".other-bubble-"+spreadGraph.queue[price][user]).remove();
                        spreadGraph.spread_svg.append("circle")
                        .attr("cx", (spreadGraph.spread_width / 2) + 35 + xOffset)
                        .attr("cy", svgMiddleY - yCoordinate)
                        .attr("r", 5)
                        .attr("class","queue other-bubble " + "other-bubble-" + spreadGraph.queue[price][user]);
                    }
                    xOffset = xOffset + 14;
                }
            }
        }   
      }
    

    

    /*
    * Starts the batch timer called on batch begins message
    */
    startBatchTimer(){
        //Batch Timer for FBA
        spreadGraph.spread_svg.append("rect")
        .attr("id", "remove")
        .attr("x", 0)
        .attr("width", spreadGraph.spread_width)
        .attr("y", spreadGraph.spread_height)
        .attr("height", 25)
        .attr("class", "my-batch-flash")
        .transition().duration(5000).style("opacity", 0);
    }

    /*
    * Updating Spread Lines on the spread graph at a time of a batch processed
    */
    updateFBASpreadGraphLines(){
        spreadGraph.spreadLinesFBABatch = {};
        for(var key in spreadGraph.spreadLinesFBAConcurrent){
            spreadGraph.spreadLinesFBABatch[key] = spreadGraph.spreadLinesFBAConcurrent[key];
            spreadGraph.drawSpreadChange(spreadGraph.spreadLinesFBAConcurrent);
        }
   }

    clear(){
      spreadGraph.spread_svg.selectAll(".my_line").remove();
      spreadGraph.spread_svg.selectAll(".others_line").remove();
      spreadGraph.spread_svg.selectAll("rect").remove();
    }
    updateBidAndAsk(bid,offer){
            spreadGraph.bestBid = bid;
            spreadGraph.bestOffer = offer;

            // document.querySelector('info-table').querySelector('curr_bid').innerHTML = bid;
            // document.querySelector('info-table').querySelector('curr_ask').innerHTML = offer; 
    }
    updateUserBidAndAsk(price,side){
        if(side == "B"){
            // document.querySelector('info-table').user_bid = price;
        } else if(side == "S"){
            // document.querySelector('info-table').user_offer = price;
        }
}

    drawBatchFlash(){
        //Flash purple on border whenever a batch message is recieved from the exchange
        spreadGraph.spread_svg.transition().style("border","solid purple 3px").duration(0);
        spreadGraph.spread_svg.transition().style("border","none").delay(400);
    }
  }

window.customElements.define('spread-graph', SpreadGraph);
