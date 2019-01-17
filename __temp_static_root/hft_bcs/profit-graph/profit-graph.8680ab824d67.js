import {html, PolymerElement}  from '../node_modules/@polymer/polymer/polymer-element.js';

/**
 * @customElement
 * @polymer
 */
class ProfitGraph extends PolymerElement {
  constructor(){
    super();
    profitGraph.shadow_dom = document.querySelector("profit-graph").shadowRoot;
    profitGraph.shadow_dom.innerHTML = `
<style>
    .batch-line {
        stroke: #a7a7a7;
        stroke-width: 3px;
    }

    .batch-label-text {
        fill: rgb(150, 150, 150);
        font-size: 10px;
        -webkit-user-select: none;
        cursor: default;
    }
    .time-grid-box-dark {
        fill: rgb(211, 211, 211);
    }
    
    .time-grid-line-text {
        fill: rgb(150, 150, 150);
        font-size: 10px;
        -webkit-user-select: none;
        cursor: default;
    }
    
    .price-grid-line {
        stroke: rgb(230, 230, 230);
        stroke-width: 1;
    }
    
    .price-grid-line-zero {
        stroke: rgb(168, 168, 168);
        stroke-width: 1;
    }
    
    .price-grid-line-text {
        fill: rgb(150, 150, 150);
        font-size: 10px;
        -webkit-user-select: none;
        cursor: default;
    }
    
    .my-profit-out {
        stroke: rgb(110, 110, 110);
        stroke-width: 3;
    }
    
    .my-profit-snipe {
        stroke: rgb(200, 79, 34);
        stroke-width: 3;
    }
    
    .my-profit-maker {
        stroke: rgb(26, 73, 232);
        stroke-width: 3;
    }
    
    .my-positive-profit {
        stroke: green;
        stroke-width: 2;
    }
    
    .my-negative-profit {
        stroke: red;
        stroke-width: 2;
    }
</style>

<svg id="profit-graph"></svg>
    `;

    /*
     * Debug variables
     */
    profitGraph.debug = {
        "calcTimeGridLines"    :false,
        "secondTick"           :false,
    };
    /*
     * set of variables we added that were not part of the original solution
     */
    profitGraph.maxSpread = otree.maxSpread;
    
    /*
     * Set of variables we update from oTree and manifest values 
     */ 
    profitGraph.startingWealth =   otree.startingWealth; 
    profitGraph.profit = profitGraph.startingWealth;                                           // Through Django Channels// Django Query
    profitGraph.profitElementWidth = profitGraph.profit_width;
    profitGraph.profitElementHeight = profitGraph.profit_height;
    profitGraph.slowDelay = 5e8;
    profitGraph.fastDelay = 1e8;

    profitGraph.profitGraph_svg = profitGraph.shadow_dom.querySelector("#profit-graph");

    
    /*
     * HTML Variables
     */ 
    profitGraph.profitGraph_svg.style.width = profitGraph.profit_width;
    profitGraph.profitGraph_svg.style.height = profitGraph.profit_height;
    
    /*
     * d3 Variables
     */ 
    profitGraph.profitSVG = d3.select(profitGraph.profitGraph_svg);
    profitGraph.curTimeX = 0;

    /*
     * Variables for time calculation
     */

    profitGraph.nanoToSec = 1e9;
    profitGraph.secToNano = 1e-9
    profitGraph.million = 1e6;
    profitGraph.timeOffset = 0;        //offset to adjust for clock difference between lab computers
    profitGraph.timeInterval = 60e9;   //current amount in seconds displayed at once on full time axis
    profitGraph.timeIncrement =  5e9;  // Amount in nanoseconds between lines on time x-axis
    profitGraph.timeSinceStart = 0;    //the amount of time since the start of the experiment in nanoseconds
    profitGraph.nanosecondPerPixel = 0;// number of ms represented by one pixel
    profitGraph.advanceTimeShown = 0;  // the amount of time shown to the right of the current time on the graph


    // maybe spread on profit graph
    profitGraph.priceRange =  5*otree.maxSpread;
    profitGraph.maxPriceProfit = profitGraph.startingWealth + (profitGraph.priceRange / 2);
    profitGraph.minPriceProfit = profitGraph.startingWealth - (profitGraph.priceRange / 2);
    profitGraph.centerPriceProfit = (profitGraph.maxPriceProfit + profitGraph.minPriceProfit) / 2;
   
    profitGraph.profitJumps = [];

    profitGraph.batchLength = otree.batchLength * 1000000000;
    profitGraph.batchLines = [];

    //------------------------------------------------
    profitGraph.axisLabelWidth = 40;    //used                                  //Width of area where price axis labels are drawn
    profitGraph.graphPaddingRight = 50;  //used                                 // how far from the x axis label that the line stops moving
    profitGraph.graphAdjustSpeedProfit = 100;                              //speed that profit price axis adjusts in pixels per frame
    profitGraph.numberOfTicks = 10;
    profitGraph.profitPriceGridIncrement = 10;                             //amount between each line on profit price axis
    
    profitGraph.currentTime = 0;                                          // Time displayed on graph
    profitGraph.profitPriceLines = [];                                    // The array of price lines
    profitGraph.timeLines = [];
    profitGraph.pricesArray = [];
   
    
    
    profitGraph.marketZoomLevel = 4;                                      // current zoom level for each graph
    profitGraph.profitZoomLevel = 4;
    profitGraph.maxZoomLevel = 4;                                         // maximum allowed zoom level
    profitGraph.zoomAmount = 0;                                           // amount zoomed per click
    profitGraph.expandedGraph = false;
    profitGraph.prevMaxPriceMarket = 0;                                   // storage for previous max and min values for when graph is in expanded mode
    profitGraph.prevMinPriceMarket = 0;
    profitGraph.prevMaxPriceProfit = 0;
    profitGraph.prevMinPriceProfit = 0;
    profitGraph.op = 1;                                                  //added 7/24/17 for adding opacity to transaction lines
    profitGraph.currentTransaction = null;                               //added 7/24/17 for ensuring only the correct orders are drawn as transacted
    profitGraph.currTransactionID = null;                                //added 7/24/17 for ensuring only the correct orders are drawn as transacted
    profitGraph.heightScale = .4;                                        //added 7/26/17 to shift the height of the graph to fit buttons under
    profitGraph.widthScale = 0;                                          //added 7/28/17 to widen the graphs of ticks to be better fit spread 
    profitGraph.oldFundPrice = null;
    profitGraph.FPCop = 1;
    profitGraph.currSpreadTick = 0;
    profitGraph.startTime = 0;
    profitGraph.tickAnimationID = 0;
    profitGraph.staticTickAnimationID = 0;
    profitGraph.laser = true;                                            //magic
    profitGraph.removeStartTime = 0;
    profitGraph.removeAnimationID = 0;
    profitGraph.removeStaticAnimationID = 0;
    profitGraph.IDArray = [];
    profitGraph.FPCswing = null;                                        //used for shifting spread ticks with FPC's
    profitGraph.currentSellTick = [];
    profitGraph.currentBuyTick = [];
    profitGraph.PreviousProfit = 0;

    /*
    Functions tied to the Profit Graph
    */
    profitGraph.calcPriceGridLines = this.calcPriceGridLines;
    profitGraph.calcTimeGridLines = this.calcTimeGridLines;
    profitGraph.getTime = this.getTime;
    profitGraph.mapTimeToXAxis = this.mapTimeToXAxis;
    profitGraph.mapProfitPriceToYAxis = this.mapProfitPriceToYAxis;
    profitGraph.calcPriceBounds = this.calcPriceBounds;
    profitGraph.millisToTime = this.millisToTime;
    profitGraph.drawTimeGridLines = this.drawTimeGridLines;
    profitGraph.drawPriceGridLines = this.drawPriceGridLines;
    profitGraph.drawPriceAxis = this.drawPriceAxis;
    profitGraph.drawProfit = this.drawProfit;
    profitGraph.draw = this.draw;
    profitGraph.calcBatchLines = this.calcBatchLines; 
    profitGraph.drawBatchLines = this.drawBatchLines;
    profitGraph.clear = this.clear;
    profitGraph.addProfitJump = this.addProfitJump;
    profitGraph.init =  this.init;
  }

  calcPriceGridLines(maxPrice,minPrice,increment){
    var gridLineVal = minPrice + increment - (minPrice % increment);
    // adjust for mod of negative numbers not being negative
    if(minPrice < 0){
      gridLineVal -= increment;
    }
        var lines = [];
        while (gridLineVal < maxPrice) {
            lines.push(gridLineVal);
            gridLineVal += increment;
        }
        return lines;  
    }

    calcTimeGridLines(startTime, endTime, increment){
        if(profitGraph.debug["calcTimeGridLines"]){
            console.log("Call to calculate calTimeGrindLines with scaled values\n   startTime:  " + (startTime / profitGraph.nanoToSec).toFixed(2) + 
                "\n   endTime:    " + (endTime / profitGraph.nanoToSec).toFixed(2) + 
                "\n   difference: " + ((endTime - startTime) / profitGraph.nanoToSec).toFixed(2) + 
                "\n   increment:  " + (increment / profitGraph.nanoToSec) + 
                "\n   adminStart: " + (profitGraph.adminStartTime / profitGraph.nanoToSec).toFixed(2));
        }
        // var timeLineVal = startTime + increment;
        var timeLineVal = startTime - ((startTime - profitGraph.adminStartTime) % increment);
        var lines = [];
        while (timeLineVal < endTime) {
            lines.push(timeLineVal);
            timeLineVal += increment;
        }
        if(profitGraph.debug["calcTimeGridLines"]){
            console.log("Lines post computation: previous set of lines :-: computed set of lines ");
            for(var i = 0; i < lines.length; i++){
                console.log("   [" + i + "]    " + ((profitGraph.timeLines[i] - profitGraph.adminStartTime) / profitGraph.nanoToSec).toFixed(2) + "  :-:  " + ((lines[i] - profitGraph.adminStartTime) / profitGraph.nanoToSec).toFixed(2));
            }
        }
        return lines;
    }

    getTime(){
      var now = new Date(),
      then = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate(),
        0,0,0),
        diff = now.getTime() - then.getTime();
        diff *= 1000000;
        return diff;
    }


    mapTimeToXAxis(timeStamp) {
        var percentOffset;
        if (profitGraph.timeSinceStart >= profitGraph.timeInterval) {
            percentOffset = (timeStamp - (profitGraph.currentTime - profitGraph.timeInterval)) / (profitGraph.timeInterval);
        }else {
            percentOffset = (timeStamp - profitGraph.adminStartTime) / profitGraph.timeInterval;
        }
        return (profitGraph.profitElementWidth - profitGraph.axisLabelWidth - profitGraph.graphPaddingRight) * percentOffset;   //changed 7/27/17
    }

    mapProfitPriceToYAxis(price) {
        // percent distance from maxPriceProfit
        var percentOffset = (profitGraph.maxPriceProfit - price) / (profitGraph.maxPriceProfit - profitGraph.minPriceProfit);
        // value of the percent offset from top of graph
        return profitGraph.profitElementHeight * percentOffset;      //changed 7/27/17 to fix profit graph
    }

    calcPriceBounds() {
        //calc bounds for profit graph
        if (profitGraph.profit > (.2 * profitGraph.minPriceProfit) + (.8 * profitGraph.maxPriceProfit) ||
            profitGraph.profit < (.8 * profitGraph.minPriceProfit) + (.2 * profitGraph.maxPriceProfit)) {
            profitGraph.centerPriceProfit = profitGraph.profit;
        }
        // what is set now
        var curCenterProfit = (profitGraph.maxPriceProfit + profitGraph.minPriceProfit) / 2;
        if (Math.abs(profitGraph.centerPriceProfit - curCenterProfit) > 1000) {
            profitGraph.profitPriceLines = profitGraph.calcPriceGridLines(profitGraph.maxPriceProfit, profitGraph.minPriceProfit, profitGraph.profitPriceGridIncrement);
            //adjust per frame what the max and min should be
            if (profitGraph.centerPriceProfit > curCenterProfit) {
               var diff = (profitGraph.centerPriceProfit - curCenterProfit)/10000;
               profitGraph.maxPriceProfit += profitGraph.graphAdjustSpeedProfit * diff;
               profitGraph.minPriceProfit += profitGraph.graphAdjustSpeedProfit * diff;
            } else {
                var diff =  Math.abs(profitGraph.centerPriceProfit - curCenterProfit)/10000;
               profitGraph.maxPriceProfit -= profitGraph.graphAdjustSpeedProfit * diff;
               profitGraph.minPriceProfit -= profitGraph.graphAdjustSpeedProfit * diff;
            }
        }
    }

    millisToTime(timeStamp) {
        // take nano to seconds
        var secs = (timeStamp - profitGraph.adminStartTime) / profitGraph.nanoToSec;
        var mins = Math.trunc(secs / 60);
        secs %= 60;
        return mins + ":" + ("00" + secs).substr(-2, 2);
    }

    drawTimeGridLines() {
        

profitGraph.profitSVG.selectAll("rect.time-grid-box-dark")
            .data(profitGraph.timeLines)
            .enter()
            .append("rect")
            .filter(function (d) {
                // only draw elements that are an even number of increments from the start
                return ((d - profitGraph.adminStartTime) / (profitGraph.timeIncrement)) % 2 == 0;
            })
            .attr("x", function (d) {
               return profitGraph.mapTimeToXAxis(d);
            })
            .attr("y", 0)
            // width of a sinle timeIncrement should be 5 secs ?
            .attr("width", profitGraph.timeIncrement / profitGraph.timeInterval * (profitGraph.profitElementWidth - profitGraph.axisLabelWidth - profitGraph.graphPaddingRight))   
            .attr("height", profitGraph.profitElementHeight)
            .attr("class", "time-grid-box-dark");

         //Draw labels for time grid lines
         profitGraph.profitSVG.selectAll("text.time-grid-line-text")
            .data(profitGraph.timeLines)
            .enter()
            .append("text")
            .attr("text-anchor", "start")
            .attr("x", function (d) {
               return profitGraph.mapTimeToXAxis(d) + 5 ;
            })
            .attr("y", profitGraph.profitElementHeight - 5)
            .text(function (d) {
               return profitGraph.millisToTime(d);
            })
            .attr("class", "time-grid-line-text");
    }
    calcBatchLines(startTime, endTime, increment){
        var timeLineVal = startTime - ((startTime - profitGraph.adminStartTime) % increment);
        var lines = [];

         while (timeLineVal < endTime) {
            lines.push(timeLineVal);
            timeLineVal += increment;
         }
         return lines;
    }

    drawBatchLines(){

        profitGraph.profitSVG.selectAll("line.batch-line")
                            .data(profitGraph.batchLines)         
                            .enter()
                            .append("line")
                            .attr("id","REMOVE")
                            .attr("x1", function (d) {
                            return profitGraph.mapTimeToXAxis(d);
                            })
                            .attr("x2", function (d) {
                            return profitGraph.mapTimeToXAxis(d);
                            })
                            .attr("y1", 0)
                            .attr("y2", profitGraph.profitElementHeight)
                            .attr("class", "batch-line");

        profitGraph.profitSVG.selectAll("text.batch-label-text")
                            .data(profitGraph.batchLines)
                            .enter()
                            .append("text")
                            .attr("id","REMOVE")
                            .attr("text-anchor", "start")
                            .attr("x", function (d) {
                            return profitGraph.mapTimeToXAxis(d) + 5;
                            })
                            .attr("y", profitGraph.profitElementHeight - 5)
                            .text(function (d) {
                            return profitGraph.millisToTime(d)
                            })
                            .attr("class", "batch-label-text");

    }

    drawPriceGridLines(priceMapFunction) {

        profitGraph.profitSVG.selectAll("line.price-grid-line")
            .data(profitGraph.profitPriceLines)
            .enter()
            .append("line")
            .attr("x1", 0)
            .attr("x2", profitGraph.profitElementWidth - profitGraph.axisLabelWidth)        //changed 7/27/17
            .attr("y1", function (d) {
                return profitGraph.mapProfitPriceToYAxis(d);
            })
            .attr("y2", function (d) {
                return profitGraph.mapProfitPriceToYAxis(d);
            })
            .attr("class", function (d) {
                return d != 0 ? "price-grid-line" : "price-grid-line-zero";
        });
    }
    drawPriceAxis(){
        profitGraph.profitSVG.selectAll("text.price-grid-line-text")
            .data(profitGraph.profitPriceLines)
            .enter()
            .append("text")
            .attr("text-anchor", "start")
            .attr("x", profitGraph.profitElementWidth - profitGraph.axisLabelWidth + 12)  // << why this fuck is this 12
            .attr("y", function (d) {  
               return profitGraph.mapProfitPriceToYAxis(d) + 3;
            })
            .attr("class", "price-grid-line-text")
            .text(function (d) {
                return d * (1e-4);
        });
    }

    drawProfit(historyDataSet, profitJumps) {
       
        profitGraph.profitSVG.selectAll("line.my-profit-out line.my-profit-maker line.my-profit-snipe")
            .data(historyDataSet, function (d) {   
            // historyDataSet structure = [[startTime, endTime, startProfit, endProfit, state],...] 
               return d;
            })
            .enter()
            .append("line")
            .filter(function (d) {
               return d.endTime >= (profitGraph.currentTime - profitGraph.timeInterval);
            })
            .attr("x1", function (d) {
               return profitGraph.mapTimeToXAxis(d.startTime);
            })
            .attr("x2", function (d) {
               return profitGraph.mapTimeToXAxis(d.endTime);
            })
            .attr("y1", function (d) {
               return profitGraph.mapProfitPriceToYAxis(d.startProfit);
            })
            .attr("y2", function (d) {
               document.querySelector('info-table').setAttribute("profit",(d.endProfit*(1e-4)).toFixed(2)); 
               return profitGraph.mapProfitPriceToYAxis(d.endProfit);
            })
            .attr("class", function (d) {
               // a masterpiece // no fuck you // hey thats not nice
               return d.state == "OUT" ? "my-profit-out" : (d.state == "MAKER" ? "my-profit-maker" : "my-profit-snipe");
        });

        profitGraph.profitSVG.selectAll("line.positive-profit line.negative-profit")
            .data(profitJumps)      
            // profitJumps structure = {timestamp:(nano), newPrice:(thousands), oldPrice:(thousands)}    
            .enter()
            .append("line")
            .filter(function (d) {
               return d.timestamp >= (profitGraph.currentTime - profitGraph.timeInterval);
            })
            .attr("x1", function (d) {
               return profitGraph.mapTimeToXAxis(d.timestamp);
            })
            .attr("x2", function (d) {
               return profitGraph.mapTimeToXAxis(d.timestamp);
            })
            .attr("y1", function (d) {
               return profitGraph.mapProfitPriceToYAxis(d.oldProfit);     //old profit
            })
            .attr("y2", function (d) {
               return profitGraph.mapProfitPriceToYAxis(d.newProfit);     //current profit
            })
            .attr("class", function (d) {
                  return d.oldProfit < d.newProfit ? "my-positive-profit" : "my-negative-profit";
            });   
    }

    addProfitJump(obj){
        var timeNow = profitGraph.getTime();
        var profit = 0;
        /*
            CALCULATE PROFIT BASED ON THE FUNCTION GIVEN ON ASANA
        */
        var expectedPrice = (obj["order_token"][4] == "S" ) ? spreadGraph.bestBid: spreadGraph.bestOffer;
        var myCashPosition = obj["endowment"];
        var endowment = myCashPosition + expectedPrice*obj["inventory"];
 
        var profit = currentProfit + endowment*(1e-4);
 
        
        profitGraph.profitJumps.push(
            {
                timestamp:timeNow,
                oldProfit:profitGraph.profit,
                newProfit:profitGraph.profit + profit, 
            }
        );

        profitGraph.profit += profit;
        profitGraph.profitSegments.push(
            {
                startTime:timeNow,
                endTime:timeNow, 
                startProfit:profitGraph.profit, 
                endProfit:profitGraph.profit,
                state:"maker"
            }
        )
    }

    draw(){
        //Clear the svg elements
        profitGraph.profitSVG.selectAll("*").remove();
        // the current time relative to the backend of otree; graph.timeOffset during the transition
        // is 0, but eventually we will calculate per player what the delay over django channels is 

        profitGraph.currentTime =  profitGraph.getTime() - profitGraph.timeOffset; 
        profitGraph.timeSinceStart = profitGraph.currentTime - profitGraph.adminStartTime;
        // Print to console.log everytime a second occurs
        if((profitGraph.previousTime != Math.trunc(profitGraph.timeSinceStart / profitGraph.nanoToSec)) && profitGraph.debug["secondTick"]){
            profitGraph.previousTime = Math.trunc(profitGraph.timeSinceStart / profitGraph.nanoToSec);
        } 
        
        profitGraph.curTimeX = profitGraph.mapTimeToXAxis(profitGraph.currentTime);

        // recalculate market price bounds
        profitGraph.calcPriceBounds();
        if(otree.FBA == false){
            // recalculate if virtual right side of graph is more than a graph.timeIncrement past last graph.timeLine line
            var rightSideOfGraph = profitGraph.timeLines[profitGraph.timeLines.length - 1] + profitGraph.timeIncrement;

            if (profitGraph.currentTime + profitGraph.advanceTimeShown > rightSideOfGraph){
                
                var startTime = profitGraph.currentTime - profitGraph.timeInterval;
                var endTime = profitGraph.currentTime + profitGraph.advanceTimeShown;
                profitGraph.timeLines = profitGraph.calcTimeGridLines(startTime, endTime, profitGraph.timeIncrement);
            }
            profitGraph.drawTimeGridLines();
        } else if(otree.FBA == true) {
            if (profitGraph.currentTime + profitGraph.advanceTimeShown > profitGraph.batchLines[profitGraph.batchLines.length - 1] + profitGraph.batchLength ||
                Math.max(profitGraph.adminStartTime, profitGraph.currentTime - profitGraph.timeInterval) < profitGraph.batchLines[0] - profitGraph.batchLength) {
                profitGraph.batchLines = profitGraph.calcBatchLines(profitGraph.currentTime - profitGraph.timeInterval, profitGraph.currentTime + profitGraph.advanceTimeShown, profitGraph.batchLength);      ////changed to *1000000 4/17/17 line 497
            }else{
                profitGraph.batchLines = profitGraph.calcBatchLines(profitGraph.currentTime - profitGraph.timeInterval, profitGraph.currentTime + profitGraph.advanceTimeShown, profitGraph.batchLength);    //remember to take this out 4/17/17
            }

            profitGraph.drawBatchLines();
        }
        
        profitGraph.drawPriceGridLines();
        profitGraph.drawPriceAxis();

        var speed = inputSection.inputSectionShadowDOM.querySelector(".slider-speed").checked;
        /* *****************************************************************************
        * Data Structures present in Redwood front end, and need to be adapted to otree 
        ******************************************************************************/ 

    // historyDataSet = [[startTime, endTime, startProfit, endProfit, state],...] 
    // 2-D array where each index contains a different portion of the profit line *over the entire experiment*
    // Each index has a startTime (nano), endTime (nano), startProfit (thousands), endProfit (thousands) 
    profitGraph.profitSegments[profitGraph.profitSegments.length - 1]["endTime"] = profitGraph.currentTime;
    
    var profitDecrement = 0;
    if(speed){
        profitDecrement = (profitGraph.profitSegments[profitGraph.profitSegments.length - 1]["endTime"] - profitGraph.profitSegments[profitGraph.profitSegments.length - 1]["startTime"]) * -(otree.speedCost);
    }


    profitGraph.profitSegments[profitGraph.profitSegments.length - 1]["endProfit"] = profitGraph.profitSegments[profitGraph.profitSegments.length - 1]["startProfit"] + profitDecrement;
    profitGraph.profit = profitGraph.profitSegments[profitGraph.profitSegments.length - 1]["startProfit"] + profitDecrement;
    profitGraph.drawProfit(profitGraph.profitSegments, profitGraph.profitJumps);

        if(otree.endMsg == "off"){
            requestAnimationFrame(profitGraph.draw);
        } else {
            profitGraph.clear();
        }
    }

    clear(){
        //Clear the svg elements
        profitGraph.profitSVG.selectAll("*").remove();
    }

    init(startFP, startingWealth) {
        for(var i = 2; i < arguments.length; i++){
            profitGraph.debug[arguments[i]] = true;
        }
        profitGraph.previousTime = 0;
        // nanoseconds per picxel 
        profitGraph.nanosecondPerPixel = profitGraph.timeInterval / (profitGraph.profitElementWidth - profitGraph.axisLabelWidth - profitGraph.graphPaddingRight);   
        // the amount of nano taken up by the axisLabelWidth ad graphPadding right
        profitGraph.advanceTimeShown = profitGraph.nanosecondPerPixel * (profitGraph.axisLabelWidth + profitGraph.graphPaddingRight);
        // collect an array of price values where the horizontal lines will be drawn
        profitGraph.profitPriceLines = profitGraph.calcPriceGridLines(profitGraph.maxPriceProfit, profitGraph.minPriceProfit, profitGraph.profitPriceGridIncrement);
        console.log(profitGraph.profitPriceLines );
        var endTime = profitGraph.adminStartTime + profitGraph.timeInterval + profitGraph.advanceTimeShown;
        profitGraph.timeLines = profitGraph.calcTimeGridLines(profitGraph.adminStartTime, endTime, profitGraph.timeIncrement);
        profitGraph.batchLines = profitGraph.calcBatchLines(profitGraph.adminStartTime, profitGraph.adminStartTime + profitGraph.timeInterval + profitGraph.advanceTimeShown, profitGraph.batchLength);
    }
}

window.customElements.define('profit-graph', ProfitGraph);
