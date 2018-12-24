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

    spreadGraph.spread_width = document.querySelector("interactive-component").clientWidth;
    spreadGraph.spread_height = document.querySelector("interactive-component").clientHeight*0.4;

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
  <path d="M2,2 L10,6 L2,10 L2,2 L2,2" style="fill: #309930;"></path>
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
  <path d="M2,2 L10,6 L2,10 L2,2 L2,2" style="fill: #CB1C36;"></path>
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
    spreadGraph.updateBidAndAsk = this.updateBidAndAsk;
    spreadGraph.drawBatchFlash = this.drawBatchFlash;
    spreadGraph.startBatchTimer = this.startBatchTimer;
    spreadGraph.drawPossibleSpreadTicks = this.drawPossibleSpreadTicks;
    spreadGraph.updateFBASpreadGraphLines = this.updateFBASpreadGraphLines;
    spreadGraph.drawLineAttempt = this.drawLineAttempt;
    spreadGraph.drawFPC = this.drawFPC;
    spreadGraph.executionHandler = this.executionHandler;
    spreadGraph.drawSpreadChange = this.drawSpreadChange;
    spreadGraph.mapSpreadGraph = this.mapSpreadGraph;
    spreadGraph.drawArrows = this.drawArrows;
    spreadGraph.dragArrow = this.dragArrow;

    /*
        price: price it is pointed at
        d3 arrow line: line created in d3 that maps to yCoordinate to price just above
        textline : text d3 function for "bid" or "ask"
    */
    spreadGraph.bidArrow = {};
    spreadGraph.askArrow = {};

    
    //Creating the start state
    spreadGraph.start();
    
    //Activating the event listener
    // spreadGraph.listen();
    //spreadGraph.mapSpreadGraph();


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
    spreadGraph.drawArrows();  
  }

  /*
   *  Map the user click of the spread click to a price then sends that spread to the backend
   */
//   listen(){
//     spreadGraph.spread_svg.on('click',function(d) {
//       spreadGraph.svg_y_offset = spreadGraph.spread_graph_shadow_dom.querySelector("#spread-graph").getBoundingClientRect().top;
//       var role = document.querySelector('info-table').player_role;
//         if(role == "MAKER"){
//             var svg_middle_x = spreadGraph.spread_width / 2;
//             var fp_line_y = spreadGraph.spread_height / 2;
            
//             var clicked_point = {
//                 x:(d3.event.clientX ),
//                 y:(d3.event.clientY - spreadGraph.svg_y_offset)
//             };

//             var distance_from_middle = Math.abs((clicked_point.y) - fp_line_y);
//             var ratio = distance_from_middle / (spreadGraph.spread_height/2);
//             var my_spread = (ratio*otree.maxSpread).toFixed(0);
//             var svg_middle_y = spreadGraph.spread_height/2;


//             if(my_spread < otree.min_spread){
//                 //enforce a minimum spread
//                 my_spread = otree.min_spread;
//             }   
            
//             var money_ratio =  otree.maxSpread/my_spread;

//             var y_coordinate = svg_middle_y/money_ratio;

//             spreadGraph.drawLineAttempt(y_coordinate);

//             if(otree.IEX == true){
//                 //Choose one of the spread lines that
//                 for(var i = 0; i < spreadGraph.possibleSpreadLines.length; i++){                
//                     if(my_spread < spreadGraph.possibleSpreadLines[i]){
//                         my_spread = spreadGraph.possibleSpreadLines[i-1];
//                         break;
//                     }
//                 }
//             }

//             spreadGraph.sendSpreadChange(my_spread);
//           } 
//     });
//   }

  drawArrows(){
      //Green Bid --> #B2D8B2
      //Red ask --> #FFB2B2
      spreadGraph.bidArrow["price"] = 940000;
      spreadGraph.askArrow["price"] = 960000;

    spreadGraph.bidArrow["bidArrowLine"] = spreadGraph.spread_svg.append("line")
        .attr("x1",spreadGraph.visibleTickLines[spreadGraph.bidArrow["price"]])  
        .attr("y1",spreadGraph.spread_height - 25)  
        .attr("x2",spreadGraph.visibleTickLines[spreadGraph.bidArrow["price"]])  
        .attr("y2",spreadGraph.spread_height*0.6 + 20)  
        .attr("stroke","#309930")  
        .attr("stroke-width",7)  
        .attr("marker-end","url(#bidArrow)")
        .call(d3.drag()
            .on("drag", function(){
                //Making sure not to drag past other arrow line
                var lineX = (spreadGraph.askArrow["askArrowLine"].attr("x1") - 10 <= d3.event.x) ? spreadGraph.askArrow["askArrowLine"].attr("x1") - 10: d3.event.x ;
                spreadGraph.bidArrow["bidArrowText"].attr("x", lineX);
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
                   spreadGraph.bidArrow["bidArrowText"].attr("x", checkedX);
                    spreadGraph.bidArrow["bidArrowLine"].attr("x1",  checkedX).attr("x2", checkedX);

                }   
            )
          
    );
        
    spreadGraph.askArrow["askArrowLine"] = spreadGraph.spread_svg.append("line")
        .attr("x1",spreadGraph.visibleTickLines[spreadGraph.askArrow["price"]])  
        .attr("y1",spreadGraph.spread_height - 25)  
        .attr("x2",spreadGraph.visibleTickLines[spreadGraph.askArrow["price"]])  
        .attr("y2",spreadGraph.spread_height*0.6 + 20)  
        .attr("stroke","#CB1C36")  
        .attr("stroke-width",7)  
        .attr("marker-end","url(#askArrow)")
        .call(d3.drag()
            .on("drag", function(){
                //Making sure not to drag past other arrow line
                var lineXAsk = (+spreadGraph.bidArrow["bidArrowLine"].attr("x1") + 10 >= d3.event.x) ? +spreadGraph.bidArrow["bidArrowLine"].attr("x1") + 10: d3.event.x ;
                console.log(lineXAsk);
                spreadGraph.askArrow["askArrowText"].attr("x", lineXAsk);
                spreadGraph.askArrow["askArrowLine"].attr("x1",  lineXAsk).attr("x2", lineXAsk);
            })
            .on("end", function(){
                    //finding the price in which is just past the dropped x value
                    var xAsk = +spreadGraph.askArrow["askArrowLine"].attr("x1");
                    console.log(xAsk);
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
                    console.log(snappedXAsk, snappedPriceAsk);
                    //Check for ask line x making sure it cant snap to other line 
                    var checkedXAsk = (+spreadGraph.bidArrow["bidArrowLine"].attr("x1") == snappedXAsk) ? spreadGraph.visibleTickLines[tickArray[i]] : snappedXAsk;
                    var checkedPriceAsk = (+spreadGraph.bidArrow["bidArrowLine"].attr("x1") == snappedXAsk) ? tickArray[i] : snappedPriceAsk;
                    
                    spreadGraph.askArrow["price"] = checkedPriceAsk;
                    /*
                        //SEND spreadGraph.askArrow["askArrowLine"].price OVER SOCKET ********* 
                    */
                    spreadGraph.askArrow["askArrowText"].attr("x", checkedXAsk);
                    spreadGraph.askArrow["askArrowLine"].attr("x1",  checkedXAsk).attr("x2", checkedXAsk);

                }   
            )
            
    );

    spreadGraph.bidArrow["bidArrowText"]  = spreadGraph.spread_svg.append("text")
        .attr("text-anchor", "start")
        .attr("x", +spreadGraph.bidArrow["bidArrowLine"].attr("x1") - 10)  
        .attr("y",  spreadGraph.spread_height - 10)
        .attr("class", "price-grid-line-text")
        .text("BID");

    spreadGraph.askArrow["askArrowText"]  = spreadGraph.spread_svg.append("text")
        .attr("text-anchor", "start")
        .attr("x", +spreadGraph.askArrow["askArrowLine"].attr("x1") - 10)  
        .attr("y",  spreadGraph.spread_height - 10)
        .attr("class", "price-grid-line-text")
        .text("ASK");
    
        
  }


    /*
    * This is sent to replicate the time that it takes to send an order to the market
    * STILL TO DO TAKE OUT TRANSACTION SPEED
    */
    drawLineAttempt(y_coordinate){

        spreadGraph.spread_svg.selectAll(".my_line_attempt").remove();

        var svg_middle_y = spreadGraph.spread_height/2;
        //svg_middle_y y_coordinate
        var your_spread_line_top = spreadGraph.spread_svg.append("svg:line")
        .attr("x1", spreadGraph.spread_width)
        .attr("y1", svg_middle_y - y_coordinate)
        .attr("x2", spreadGraph.spread_width - 25)
        .attr("y2", svg_middle_y - y_coordinate)
        .attr("stroke-width",3)
        .attr("class","my_line_attempt");

    var your_spread_line_bottom = spreadGraph.spread_svg.append("svg:line")
        .attr("x1", spreadGraph.spread_width)
        .attr("y1", y_coordinate + svg_middle_y)
        .attr("x2", spreadGraph.spread_width - 25)
        .attr("y2", y_coordinate + svg_middle_y)
        .attr("stroke-width",3)
        .attr("class","my_line_attempt");

        var  transaction_speed = otree.speedLongDelay ;
        if(document.querySelector("info-table").speed_cost != 0){
            transaction_speed = otree.speedShortDelay;
        }

        spreadGraph.addOthersLineAnimation([your_spread_line_top, your_spread_line_bottom], transaction_speed, 25);
        your_spread_line_top.transition().delay(transaction_speed).remove();
        your_spread_line_bottom.transition().delay(transaction_speed).remove();
    }

    /*
    * IEX Specififc Function
    * Draws the possible spread ticks based on the set of possible spread ticks
    */
    drawPossibleSpreadTicks(){
    //Draws the possible spread ticks for IEX
    // var temp = parseInt(otree.min_spread);
    // var svg_middle_y = spreadGraph.spread_height/2;
    // var maxSpread = parseInt(otree.maxSpread);
    // spreadGraph.possibleSpreadLines = [];
    //     for(;temp < maxSpread;){
    //         //Every spread price is drawn and so is the price
    //         var money_ratio =  maxSpread/temp;
    //         var y_coordinate = svg_middle_y/money_ratio;
            
    //         spreadGraph.spread_svg.append("svg:line")
    //             .attr("x1", (spreadGraph.spread_width / 2) - 15)
    //             .attr("y1", svg_middle_y - y_coordinate)
    //             .attr("x2", (spreadGraph.spread_width / 2) + 15)
    //             .attr("y2", svg_middle_y - y_coordinate)
    //             .attr("stroke-width",1)
    //             .attr("class","possible-spread-ticks");
            
    //         spreadGraph.spread_svg.append("svg:line")
    //             .attr("x1", (spreadGraph.spread_width / 2) - 15)
    //             .attr("y1", svg_middle_y + y_coordinate)
    //             .attr("x2", (spreadGraph.spread_width / 2) + 15)
    //             .attr("y2", svg_middle_y + y_coordinate)
    //             .attr("stroke-width",1)
    //             .attr("class","possible-spread-ticks");        
            
    //         spreadGraph.spread_svg.append("text")
    //             .attr("text-anchor", "start")
    //             .attr("x", (spreadGraph.spread_width / 2) + 17)  
    //             .attr("y",  svg_middle_y + y_coordinate  + 3)
    //             .attr("class", "price-grid-line-text")
    //             .text((temp/10000).toFixed(2));

    //         spreadGraph.spread_svg.append("text")
    //             .attr("text-anchor", "start")
    //             .attr("x", (spreadGraph.spread_width / 2) + 17)  
    //             .attr("y",  svg_middle_y - y_coordinate + 3)
    //             .attr("class", "price-grid-line-text")
    //             .text((temp/10000).toFixed(2));
            
    //         spreadGraph.possibleSpreadLines.push(temp);
    //         spreadGraph.queue[temp] = [];
    //         temp = otree.min_spread + temp;
    //     }
        var upperBound = 1000000;
        var lowerBound =  900000;
        var diff = upperBound - lowerBound;
        var increment  =   10000;
        var incrementNum = diff / increment;
        var distanceBetweenLines = spreadGraph.spread_width/incrementNum;
        var xCoordinate = 0;
        var yCoordinate = spreadGraph.spread_height*0.3;
        spreadGraph.visibleTickLines = {};

        
        for(var temp = lowerBound; temp <= upperBound; temp+=increment){
            spreadGraph.visibleTickLines[temp] = xCoordinate;
                spreadGraph.spread_svg.append("svg:line")
                    .attr("x1", xCoordinate)
                    .attr("y1", spreadGraph.spread_height*0.3 - 15)
                    .attr("x2", xCoordinate)
                    .attr("y2", spreadGraph.spread_height*0.3 + 15)
                    .attr("stroke-width",1)
                    .attr("class","possible-spread-ticks");  
                
                spreadGraph.spread_svg.append("text")
                    .attr("text-anchor", "start")
                    .attr("x", xCoordinate - 5)  
                    .attr("y",  spreadGraph.spread_height*0.6 - 10)
                    .attr("class", "price-grid-line-text")
                    .text((temp/10000).toFixed(0));

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
    * Sending Spread Change to backend update the info-table accordingly
    */
    sendSpreadChange(my_spread = otree.defaultSpread){
    //Sending Spread Change over socket 
    var msg = {
        type: 'spread_change',
        id: otree.playerID ,
        id_in_group: otree.playerIDInGroup,
        spread: my_spread
    };
    if (socketActions.socket.readyState === socketActions.socket.OPEN) {
        socketActions.socket.send(JSON.stringify(msg));
    }
    document.querySelector('info-table').spread_value = (my_spread / 10000).toFixed(2);
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
    /*
    FUNDPRICE  = 984800
    (index):272 {id: 1, token: "SUBAS000000045", profit: 1400, orig_price: 986243, exec_price: 986243}
    (index):278 986243
    */

    executionHandler(exec = {}){
        if(otree.endMsg == "off"){

            var exec_side = exec.side;
            var exec_spread = "";
            var offset = 0;

            var userPlayerID = otree.playerIDInGroup;
            var svgMiddleY = spreadGraph.spread_height/2;
            var role = document.querySelector('info-table').player_role;
            var currentFP =  ((document.querySelector('info-table').fp)*10000).toFixed(0);      

            var  transactionSpeed = otree.speedLongDelay ;
            if(document.querySelector("info-table").speed_cost != 0){
                transactionSpeed = otree.speedShortDelay;
            }

            if(exec.player == userPlayerID ){
                console.log(exec.T0K);
                if(spreadGraph.spread_lines[userPlayerID] != undefined){
                    //you are a maker 

                    //Price to be pulled from backend messaging
                    // var priceOfTransaction = spreadGraph.spread_lines[exec.player][(exec_side == "S") ? "A" : exec_side];
                    var priceOfTransaction = exec.orig_price;
                    // console.log(priceOfTransaction + " vs. " + exec.orig_price);
                    
                    var upperPriceBound = (otree.maxSpread/2) +  +currentFP;
                    var lowerPriceBound = +currentFP - (otree.maxSpread/2) ;
                    // console.log(upperPriceBound);
                    var totalDiff = upperPriceBound - priceOfTransaction;
                    // console.log("upperBound  " + upperPriceBound + " - POT " + priceOfTransaction+ " = totalDiff " + totalDiff);
                    // console.log(totalDiff);
                    var ratio = totalDiff/otree.maxSpread;
                    var transactionYCoordinate = ratio * spreadGraph.spread_height;

                    
                
                    if(exec_side == "S"){

                        spreadGraph.spread_svg.selectAll(".my_line_top").remove();       
                        var yourSpreadLineTop = spreadGraph.spread_svg.append("svg:line")
                            .attr("x1", spreadGraph.spread_width)
                            .attr("y1",  svgMiddleY - transactionYCoordinate)
                            .attr("x2", spreadGraph.spread_width - 25)
                            .attr("y2",  svgMiddleY - transactionYCoordinate)
                            .attr("stroke-width",3)
                            .attr("class","my_line my_line_top");
                    
                        spreadGraph.addOthersLineAnimation([yourSpreadLineTop], transactionSpeed, 25);

                    } else if(exec.side == "B"){

                        spreadGraph.spread_svg.selectAll(".my_line_bottom").remove();       
                        var yourSpreadLineBottom = spreadGraph.spread_svg.append("svg:line")
                            .attr("x1", spreadGraph.spread_width)
                            .attr("y1",  transactionYCoordinate)
                            .attr("x2", spreadGraph.spread_width - 25)
                            .attr("y2",  transactionYCoordinate)
                            .attr("stroke-width",3)
                            .attr("class","my_line my_line_bottom");

                        spreadGraph.addOthersLineAnimation([yourSpreadLineBottom], transactionSpeed, 25);
                    }
                    spreadGraph.drawTransactionBar(exec_spread, svgMiddleY,transactionYCoordinate , (exec_side == "S") ? "A" : exec_side, ((exec.profit > 0) ? "transaction_bar_light_green" : "transaction_bar_light_red"), 10);


                } else {
                    //Your player client browser was the sniper
                    
                }
            } else {
                //do something else if not player just draw transaction bar with offset
                
                if(spreadGraph.spread_lines[exec.player] != undefined){
                     
                    var priceOfTransactionOther = spreadGraph.spread_lines[exec.player][(exec_side == "S") ? "A" : exec_side];
                    
                    var upperPriceBoundOther = (otree.maxSpread/2) +  +currentFP;
                    var lowerPriceBoundOther = +currentFP - (otree.maxSpread/2) ;
                    var totalDiffOther = Math.abs(upperPriceBoundOther - priceOfTransactionOther);
                    var ratioOther = totalDiffOther/otree.maxSpread;
                    var transactionYCoordinateOther = ratioOther * spreadGraph.spread_height;

                    // var userSpread = parseInt(spreadGraph.spread_lines[userPlayerID]["A"] - spreadGraph.spread_lines[userPlayerID]["B"]);
                    
                    // var moneyRatio =  otree.maxSpread/userSpread;
                    // var yCoordinate = svgMiddleY/moneyRatio;

                    spreadGraph.drawTransactionBar(exec_spread, svgMiddleY,transactionYCoordinateOther , (exec_side == "S") ? "A" : exec_side, ((exec.profit > 0) ? "transaction_bar_light_green" : "transaction_bar_light_red"), -10);

                } 
            }

        }
    }
  

  drawFPC(offset){
    //Price Jump (FPC) Offset is the price
    otree.offset = offset;
    var spread_line_fundamental_price = spreadGraph.spread_svg.append("svg:line")
        .attr("x1", 0 + 50)
        .attr("y1", spreadGraph.spread_height/2 )
        .attr("x2", spreadGraph.spread_width - 50)
        .attr("y2", spreadGraph.spread_height/2 ) 
        .style("stroke", "yellow")
        .style("stroke-width", 10)
        .attr("class", "inv-line");
    window.setTimeout(function(){
        spreadGraph.spread_svg.select(".inv-line").remove();
    },400);

    var spread_line_fundamental_price = spreadGraph.spread_svg.append("svg:line")
        .attr("x1", 0 + 60)
        .attr("y1", spreadGraph.spread_height/2 )
        .attr("x2", spreadGraph.spread_width - 60)
        .attr("y2", spreadGraph.spread_height/2)
        .attr("class", "fund-price")
        .style("stroke", "grey")
        .style("stroke-width", 3);

    var userPlayerID = otree.playerIDInGroup;
    var svgMiddleY = spreadGraph.spread_height/2;
    var role = document.querySelector('info-table').player_role;
    var  transactionSpeed = otree.speedLongDelay ;
    if(document.querySelector("info-table").speed_cost != 0){
        transactionSpeed = otree.speedShortDelay;
    }
        
    var bar_color = "";
    //if not other maker within the spread
    if(spreadGraph.smallest_spread == true){
        bar_color = "green_bar";
    }else{
        bar_color = "blue_bar";
    }

    if(otree.endMsg == "off"){
        for(var player in spreadGraph.spread_lines){
            if(player == userPlayerID){ 
                spreadGraph.spread_svg.selectAll(".my_line_top").remove();  
                spreadGraph.spread_svg.selectAll(".my_line_bottom").remove();  
                spreadGraph.spread_svg.selectAll(".spread_bar").remove();
                spreadGraph.spread_svg.selectAll(".transactionBar").remove();


                var userSpread = parseInt(spreadGraph.spread_lines[userPlayerID]["A"] - spreadGraph.spread_lines[userPlayerID]["B"]);
                var moneyRatio =  otree.maxSpread/userSpread;
                var yCoordinate = svgMiddleY/moneyRatio;
                var offsetMoneyRatio = otree.maxSpread/offset;
                var offsetYCoordinate = svgMiddleY/offsetMoneyRatio;

                var yourOffsetBottom = spreadGraph.spread_svg.append("svg:line")
                    .attr("x1", spreadGraph.spread_width)
                    .attr("y1", svgMiddleY + yCoordinate - offsetYCoordinate )
                    .attr("x2", spreadGraph.spread_width)
                    .attr("y2", svgMiddleY + yCoordinate - offsetYCoordinate)
                    .attr("stroke-width",3)
                    .attr("class","my_line my_line_bottom");

                var yourOffsetTop= spreadGraph.spread_svg.append("svg:line")
                    .attr("x1", spreadGraph.spread_width)
                    .attr("y1",  svgMiddleY - yCoordinate - offsetYCoordinate)
                    .attr("x2", spreadGraph.spread_width)
                    .attr("y2",  svgMiddleY - yCoordinate - offsetYCoordinate)
                    .attr("stroke-width",3)
                    .attr("class","my_line my_line_top");
                
                var yourBarRect = spreadGraph.spread_svg.append("svg:rect")
                    .attr("x", (spreadGraph.spread_width / 2) - 25)
                    .attr("y", spreadGraph.spread_height/2 - yCoordinate - offsetYCoordinate)
                    .attr("width", 50)
                    .attr("height", 2*yCoordinate)
                    .attr("class",bar_color + " spread_bar");

              
                
                spreadGraph.addOthersLineAnimation([yourOffsetTop,yourOffsetBottom], transactionSpeed, 25);

            } else if(player != userPlayerID){
                spreadGraph.spread_svg.selectAll(".others_line_top_" + player).remove();
                spreadGraph.spread_svg.selectAll(".others_line_bottom_" + player).remove();

                var newLineOtherSpread = parseInt(spreadGraph.spread_lines[player]["A"] - spreadGraph.spread_lines[player]["B"]);
                var newLineOtherMoneyRatio =  otree.maxSpread/newLineOtherSpread;
                var newLineOtherYCoordinate = svgMiddleY/newLineOtherMoneyRatio;
                var newOffsetMoneyRatio = otree.maxSpread/offset;
                var newOffsetYCoordinate = svgMiddleY/newOffsetMoneyRatio;

                var newLineOtherTop = spreadGraph.spread_svg.append("svg:line")
                    .attr("x1",(spreadGraph.spread_width / 2) + 15)
                    .attr("y1", svgMiddleY - newLineOtherYCoordinate - newOffsetYCoordinate)
                    .attr("x2", (spreadGraph.spread_width / 2) - 15)
                    .attr("y2", svgMiddleY - newLineOtherYCoordinate - newOffsetYCoordinate)
                    .attr("stroke-width",1)
                    .attr("class","others_line others_line_top_"+player);
                    
                var newLineOtherBottom = spreadGraph.spread_svg.append("svg:line")
                    .attr("x1", (spreadGraph.spread_width / 2) + 15)
                    .attr("y1", svgMiddleY + newLineOtherYCoordinate - newOffsetYCoordinate)
                    .attr("x2", (spreadGraph.spread_width / 2) - 15)
                    .attr("y2", svgMiddleY + newLineOtherYCoordinate - newOffsetYCoordinate)
                    .attr("stroke-width",1)
                    .attr("class","others_line others_line_bottom_"+player);
            }
        }
    }

  }

  drawSpreadChange(newLines){
      
    var userPlayerID = otree.playerIDInGroup;
    var svgMiddleY = spreadGraph.spread_height/2;
    var role = document.querySelector('info-table').player_role;
    var offset = 0;
    var newLineUserSpread = 0;
    var currentFP =  ((document.querySelector('info-table').fp)*10000).toFixed(0);    

    if(otree.endMsg == "off"){
        for(var key in newLines){
            if(key == userPlayerID){
                spreadGraph.spread_svg.selectAll(".my_line_top").remove();
                spreadGraph.spread_svg.selectAll(".my_line_bottom").remove();
                
                var priceOfTransactionTop = newLines[userPlayerID]["A"];
                var priceOfTransactionBottom = newLines[userPlayerID]["B"];
                // console.log(priceOfTransaction + " vs. " + exec.orig_price);
                
                var upperPriceBound = (otree.maxSpread/2) +  +currentFP;
                var lowerPriceBound = +currentFP - (otree.maxSpread/2) ;
                // console.log(upperPriceBound);
                var totalDiffTop = upperPriceBound - priceOfTransactionTop;
                var totalDiffBottom = upperPriceBound - priceOfTransactionBottom;
                // console.log("upperBound  " + upperPriceBound + " - POT " + priceOfTransaction+ " = totalDiff " + totalDiff);
                // console.log(totalDiff);
                var ratioForSell = totalDiffTop/otree.maxSpread;
                var ratioForBuy = totalDiffBottom/otree.maxSpread;

                var sellYCoordinate = ratioForSell * spreadGraph.spread_height;
                var buyYCoordinate = ratioForBuy * spreadGraph.spread_height;


                var newLineTop = spreadGraph.spread_svg.append("svg:line")
                            .attr("x1", (spreadGraph.spread_width / 2) + 25)
                            .attr("y1", sellYCoordinate)
                            .attr("x2", (spreadGraph.spread_width / 2) - 25)
                            .attr("y2", sellYCoordinate)
                            .attr("stroke-width",3)
                            .attr("class","my_line my_line_top");
                
                var newLineBottom = spreadGraph.spread_svg.append("svg:line")
                            .attr("x1", (spreadGraph.spread_width / 2) + 25)
                            .attr("y1", buyYCoordinate)
                            .attr("x2", (spreadGraph.spread_width / 2) - 25)
                            .attr("y2", buyYCoordinate)
                            .attr("stroke-width",3)
                            .attr("class","my_line my_line_bottom");
                
                            
                if(role == "MAKER"){
                    var transactionSpeed = otree.speedLongDelay;
                    if(document.querySelector("info-table").speed_cost != 0){
                        transactionSpeed = otree.speedShortDelay;
                    }

                    spreadGraph.drawSpreadBar(sellYCoordinate,(buyYCoordinate - sellYCoordinate));
                }

            } else{
                spreadGraph.spread_svg.selectAll(".others_line_top_" + key).remove();
                spreadGraph.spread_svg.selectAll(".others_line_bottom_" + key).remove();
                
                var newLineOtherSpread = parseInt(newLines[key]["A"] - newLines[key]["B"]);
                var newLineOtherMoneyRatio =  otree.maxSpread/newLineOtherSpread;
                var newLineOtherYCoordinate = svgMiddleY/newLineOtherMoneyRatio;
                
                var updateLineMoneyRatio = otree.maxSpread/(spreadGraph.last_spread*10000);
                var updateLineYCoordinate = svgMiddleY/updateLineMoneyRatio;
                //spreadGraph.drawSpreadBar(spreadGraph.last_spread*10000,svgMiddleY,updateLineYCoordinate, offset, userPlayerID);

                var newLineOtherTop = spreadGraph.spread_svg.append("svg:line")
                            .attr("x1",spreadGraph.spread_width)
                            .attr("y1", svgMiddleY - newLineOtherYCoordinate)
                            .attr("x2", spreadGraph.spread_width - 15)
                            .attr("y2", svgMiddleY - newLineOtherYCoordinate)
                            .attr("stroke-width",1)
                            .attr("class","others_line others_line_top_"+key);
                    
                var newLineOtherBottom = spreadGraph.spread_svg.append("svg:line")
                            .attr("x1", spreadGraph.spread_width)
                            .attr("y1", svgMiddleY + newLineOtherYCoordinate )
                            .attr("x2", spreadGraph.spread_width - 15)
                            .attr("y2", svgMiddleY + newLineOtherYCoordinate )
                            .attr("stroke-width",1)
                            .attr("class","others_line others_line_bottom_"+key);

                spreadGraph.addOthersLineAnimation([newLineOtherTop, newLineOtherBottom], 0, 15);
            }
            spreadGraph.spread_lines[key] = newLines[key];
        }



        //Updating table values with half the dollar value of the spread given above 
        if(newLineUserSpread != 0){
            spreadGraph.updateBidAndAsk(document.querySelector("info-table").fp,((newLineUserSpread/20000).toFixed(2)));
        }
    }
  }


 addOthersLineAnimation(lines, speed=500, width){

      //SETTING THE SPREAD TO THE LINE
    for(var i = 0; i < lines.length; i++){
        var add_animation = lines[i]
        .transition()
        .duration(speed)
        .attr("x1", (spreadGraph.spread_width / 2) + width)
        .attr("x2", (spreadGraph.spread_width / 2) - width);
        
    }   
    if(document.querySelector("info-table").player_role != "MAKER"){
        spreadGraph.spread_svg.selectAll("rect").remove();
        spreadGraph.spread_svg.selectAll(".my_line").remove();
   
    }   
  }

  drawSpreadBar(startY, rectHeight){
        //take into account
        var bar_color = "";
        //if not other maker within the spread
       
        if(spreadGraph.smallest_spread == true){
            bar_color = "green_bar";
        }else{
            bar_color = "blue_bar";
        }
        spreadGraph.spread_svg.selectAll(".green_bar").remove();
        spreadGraph.spread_svg.selectAll(".blue_bar").remove();
        
        var your_bar_rect = spreadGraph.spread_svg.append("svg:rect")
                   .attr("x", (spreadGraph.spread_width / 2) - 25)
                   .attr("y", startY)
                   .attr("width", 50)
                   .attr("height", rectHeight)
                   .attr("class",bar_color + " spread_bar");
}
  
    drawTransactionBar(my_spread,svg_middle_y,y_coordinate, side, color, xOffset){
        //take into account
        var bar_color = color;
        //if not other maker within the spread
        
      if(svg_middle_y <= y_coordinate){
        var your_bar_rect = spreadGraph.spread_svg.append("svg:rect")
                .attr("x", (spreadGraph.spread_width / 2) - 5 + xOffset)
                .attr("y", svg_middle_y)
                .attr("width", 5)
                .attr("height",y_coordinate - svg_middle_y)
                .attr("class","transactionBar " + bar_color);
      } else { 
        var your_bar_rect = spreadGraph.spread_svg.append("svg:rect")
            .attr("x", (spreadGraph.spread_width / 2) - 5 + xOffset)
            .attr("y", y_coordinate)
            .attr("width", 5)
            .attr("height",svg_middle_y - y_coordinate)
            .attr("class", "transactionBar " + bar_color);
      }
        // if(side == "B"){
        //     var your_bar_rect = spreadGraph.spread_svg.append("svg:rect")
        //         .attr("x", (spreadGraph.spread_width / 2) - 5 + xOffset)
        //         .attr("y", svg_middle_y)
        //         .attr("width", 5)
        //         .attr("height",y_coordinate)
        //         .attr("class",bar_color);
        // } else if(side == "S"){
        //     var your_bar_rect = spreadGraph.spread_svg.append("svg:rect")
        //             .attr("x", (spreadGraph.spread_width / 2) - 5 + xOffset)
        //             .attr("y", svg_middle_y - y_coordinate)
        //             .attr("width", 5)
        //             .attr("height", y_coordinate)
        //             .attr("class",bar_color);
        // }
        window.setTimeout(function(){
            spreadGraph.spread_svg.selectAll("." + bar_color).remove();
        },400);
    }

    clear(){
      spreadGraph.spread_svg.selectAll(".my_line").remove();
      spreadGraph.spread_svg.selectAll(".others_line").remove();
      spreadGraph.spread_svg.selectAll("rect").remove();
    }
    updateBidAndAsk(FPCDollarAmount,spread_value){
        //Updating the bid and ask on the info table
        if(document.querySelector("info-table").player_role == "MAKER"){
            var sum = +FPCDollarAmount + +spread_value;
            document.querySelector('info-table').curr_bid = parseFloat(sum).toFixed(2);
            document.querySelector('info-table').curr_ask = parseFloat(FPCDollarAmount - spread_value).toFixed(2);
        } else {
            document.querySelector('info-table').curr_bid = "N/A";
            document.querySelector('info-table').curr_ask = "N/A";
        }
    }

    drawBatchFlash(){
        //Flash purple on border whenever a batch message is recieved from the exchange
        spreadGraph.spread_svg.transition().style("border","solid purple 3px").duration(0);
        spreadGraph.spread_svg.transition().style("border","none").delay(400);
    }
  }

window.customElements.define('spread-graph', SpreadGraph);
