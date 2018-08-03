import {html, PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';
/**
 * @customElement
 * @polymer
 */
class ProfitGraph extends PolymerElement {
  constructor(){
    super();
    Profit_Graph.shadow_dom = document.querySelector("profit-graph").shadowRoot;
    Profit_Graph.shadow_dom.innerHTML = `<svg id="profit-graph"></svg>`;

    /*
     * Debug variables
     */
    Profit_Graph.debug = {
        "calcTimeGridLines"    :false,
        "secondTick"           :false,
    };
    /*
     * set of variables we added that were not part of the original solution
     */
    Profit_Graph.maxSpread = oTreeConstants.max_spread;
    
    /*
     * Set of variables we update from oTree and manifest values 
     */ 
    Profit_Graph.startingWealth =   oTreeConstants.starting_wealth; 
    Profit_Graph.profit = Profit_Graph.startingWealth;                                           // Through Django Channels// Django Query
    Profit_Graph.profitElementWidth = Profit_Graph.profit_width;
    Profit_Graph.profitElementHeight = Profit_Graph.profit_height;
    Profit_Graph.slowDelay = 5e8;
    Profit_Graph.fastDelay = 1e8;

    Profit_Graph.profit_graph_svg = Profit_Graph.shadow_dom.querySelector("#profit-graph");

    
    /*
     * HTML Variables
     */ 
    Profit_Graph.profit_graph_svg.style.width = Profit_Graph.profit_width;
    Profit_Graph.profit_graph_svg.style.height = Profit_Graph.profit_height;
    
    /*
     * d3 Variables
     */ 
    Profit_Graph.profitSVG = d3.select(Profit_Graph.profit_graph_svg);
    Profit_Graph.curTimeX = 0;

    /*
     * Variables for time calculation
     */

    Profit_Graph.nanoToSec = 1e9;
    Profit_Graph.secToNano = 1e-9
    Profit_Graph.million = 1e6;
    Profit_Graph.timeOffset = 0;        //offset to adjust for clock difference between lab computers
    Profit_Graph.timeInterval = 60e9;   //current amount in seconds displayed at once on full time axis
    Profit_Graph.timeIncrement =  5e9;  // Amount in nanoseconds between lines on time x-axis
    Profit_Graph.timeSinceStart = 0;    //the amount of time since the start of the experiment in nanoseconds
    Profit_Graph.nanosecondPerPixel = 0;// number of ms represented by one pixel
    Profit_Graph.advanceTimeShown = 0;  // the amount of time shown to the right of the current time on the graph


    // maybe spread on profit graph
    Profit_Graph.priceRange =  5*oTreeConstants.max_spread;
    Profit_Graph.maxPriceProfit = Profit_Graph.startingWealth + (Profit_Graph.priceRange / 2);
    Profit_Graph.minPriceProfit = Profit_Graph.startingWealth - (Profit_Graph.priceRange / 2);
    Profit_Graph.centerPriceProfit = (Profit_Graph.maxPriceProfit + Profit_Graph.minPriceProfit) / 2;
   
    Profit_Graph.profitJumps = [];

    //------------------------------------------------
    Profit_Graph.axisLabelWidth = 40;    //used                                  //Width of area where price axis labels are drawn
    Profit_Graph.graphPaddingRight = 50;  //used                                 // how far from the x axis label that the line stops moving
    Profit_Graph.graphAdjustSpeedProfit = 100;                              //speed that profit price axis adjusts in pixels per frame
    Profit_Graph.numberOfTicks = 10;
    Profit_Graph.profitPriceGridIncrement = Profit_Graph.priceRange / Profit_Graph.numberOfTicks;                             //amount between each line on profit price axis
    
    Profit_Graph.currentTime = 0;                                          // Time displayed on graph
    Profit_Graph.profitPriceLines = [];                                    // The array of price lines
    Profit_Graph.timeLines = [];
    Profit_Graph.pricesArray = [];
   
    
    
    Profit_Graph.marketZoomLevel = 4;                                      // current zoom level for each graph
    Profit_Graph.profitZoomLevel = 4;
    Profit_Graph.maxZoomLevel = 4;                                         // maximum allowed zoom level
    Profit_Graph.zoomAmount = 0;                                           // amount zoomed per click
    Profit_Graph.expandedGraph = false;
    Profit_Graph.prevMaxPriceMarket = 0;                                   // storage for previous max and min values for when graph is in expanded mode
    Profit_Graph.prevMinPriceMarket = 0;
    Profit_Graph.prevMaxPriceProfit = 0;
    Profit_Graph.prevMinPriceProfit = 0;
    Profit_Graph.op = 1;                                                  //added 7/24/17 for adding opacity to transaction lines
    Profit_Graph.currentTransaction = null;                               //added 7/24/17 for ensuring only the correct orders are drawn as transacted
    Profit_Graph.currTransactionID = null;                                //added 7/24/17 for ensuring only the correct orders are drawn as transacted
    Profit_Graph.heightScale = .4;                                        //added 7/26/17 to shift the height of the graph to fit buttons under
    Profit_Graph.widthScale = 0;                                          //added 7/28/17 to widen the graphs of ticks to be better fit spread 
    Profit_Graph.oldFundPrice = null;
    Profit_Graph.FPCop = 1;
    Profit_Graph.currSpreadTick = 0;
    Profit_Graph.startTime = 0;
    Profit_Graph.tickAnimationID = 0;
    Profit_Graph.staticTickAnimationID = 0;
    Profit_Graph.laser = true;                                            //magic
    Profit_Graph.removeStartTime = 0;
    Profit_Graph.removeAnimationID = 0;
    Profit_Graph.removeStaticAnimationID = 0;
    Profit_Graph.IDArray = [];
    Profit_Graph.FPCswing = null;                                        //used for shifting spread ticks with FPC's
    Profit_Graph.currentSellTick = [];
    Profit_Graph.currentBuyTick = [];
    Profit_Graph.PreviousProfit = 0;

    /*
    Functions tied to the Profit Graph
    */
    Profit_Graph.calcPriceGridLines = this.calcPriceGridLines;
    Profit_Graph.calcTimeGridLines = this.calcTimeGridLines;
    Profit_Graph.getTime = this.getTime;
    Profit_Graph.mapTimeToXAxis = this.mapTimeToXAxis;
    Profit_Graph.mapProfitPriceToYAxis = this.mapProfitPriceToYAxis;
    Profit_Graph.calcPriceBounds = this.calcPriceBounds;
    Profit_Graph.millisToTime = this.millisToTime;
    Profit_Graph.drawTimeGridLines = this.drawTimeGridLines;
    Profit_Graph.drawPriceGridLines = this.drawPriceGridLines;
    Profit_Graph.drawPriceAxis = this.drawPriceAxis;
    Profit_Graph.drawProfit = this.drawProfit;
    Profit_Graph.draw = this.draw;
    Profit_Graph.clear = this.clear;
    Profit_Graph.init =  this.init;
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
        if(Profit_Graph.debug["calcTimeGridLines"]){
            console.log("Call to calculate calTimeGrindLines with scaled values\n   startTime:  " + (startTime / Profit_Graph.nanoToSec).toFixed(2) + 
                "\n   endTime:    " + (endTime / Profit_Graph.nanoToSec).toFixed(2) + 
                "\n   difference: " + ((endTime - startTime) / Profit_Graph.nanoToSec).toFixed(2) + 
                "\n   increment:  " + (increment / Profit_Graph.nanoToSec) + 
                "\n   adminStart: " + (Profit_Graph.adminStartTime / Profit_Graph.nanoToSec).toFixed(2));
        }
        // var timeLineVal = startTime + increment;
        var timeLineVal = startTime - ((startTime - Profit_Graph.adminStartTime) % increment);
        var lines = [];
        while (timeLineVal < endTime) {
            lines.push(timeLineVal);
            timeLineVal += increment;
        }
        if(Profit_Graph.debug["calcTimeGridLines"]){
            console.log("Lines post computation: previous set of lines :-: computed set of lines ");
            for(var i = 0; i < lines.length; i++){
                console.log("   [" + i + "]    " + ((Profit_Graph.timeLines[i] - Profit_Graph.adminStartTime) / Profit_Graph.nanoToSec).toFixed(2) + "  :-:  " + ((lines[i] - Profit_Graph.adminStartTime) / Profit_Graph.nanoToSec).toFixed(2));
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
        if (Profit_Graph.timeSinceStart >= Profit_Graph.timeInterval) {
            percentOffset = (timeStamp - (Profit_Graph.currentTime - Profit_Graph.timeInterval)) / (Profit_Graph.timeInterval);
        }else {
            percentOffset = (timeStamp - Profit_Graph.adminStartTime) / Profit_Graph.timeInterval;
        }
        return (Profit_Graph.profitElementWidth - Profit_Graph.axisLabelWidth - Profit_Graph.graphPaddingRight) * percentOffset;   //changed 7/27/17
    }

    mapProfitPriceToYAxis(price) {
        // percent distance from maxPriceProfit
        var percentOffset = (Profit_Graph.maxPriceProfit - price) / (Profit_Graph.maxPriceProfit - Profit_Graph.minPriceProfit);
        // value of the percent offset from top of graph
        return Profit_Graph.profitElementHeight * percentOffset;      //changed 7/27/17 to fix profit graph
    }

    calcPriceBounds() {
        //calc bounds for profit graph
        if (Profit_Graph.profit > (.2 * Profit_Graph.minPriceProfit) + (.8 * Profit_Graph.maxPriceProfit) ||
            Profit_Graph.profit < (.8 * Profit_Graph.minPriceProfit) + (.2 * Profit_Graph.maxPriceProfit)) {
            Profit_Graph.centerPriceProfit = Profit_Graph.profit;
        }
        // what is set now
        var curCenterProfit = (Profit_Graph.maxPriceProfit + Profit_Graph.minPriceProfit) / 2;
        if (Math.abs(Profit_Graph.centerPriceProfit - curCenterProfit) > 1000) {
            Profit_Graph.profitPriceLines = this.calcPriceGridLines(Profit_Graph.maxPriceProfit, Profit_Graph.minPriceProfit, Profit_Graph.profitPriceGridIncrement);
            //adjust per frame what the max and min should be
            if (Profit_Graph.centerPriceProfit > curCenterProfit) {
               Profit_Graph.maxPriceProfit += Profit_Graph.graphAdjustSpeedProfit;
               Profit_Graph.minPriceProfit += Profit_Graph.graphAdjustSpeedProfit;
            } else {
               Profit_Graph.maxPriceProfit -= Profit_Graph.graphAdjustSpeedProfit;
               Profit_Graph.minPriceProfit -= Profit_Graph.graphAdjustSpeedProfit;
            }
        }
    }

    millisToTime(timeStamp) {
        // take nano to seconds
        var secs = (timeStamp - Profit_Graph.adminStartTime) / Profit_Graph.nanoToSec;
        var mins = Math.trunc(secs / 60);
        secs %= 60;
        return mins + ":" + ("00" + secs).substr(-2, 2);
    }

    drawTimeGridLines() {
        

Profit_Graph.profitSVG.selectAll("rect.time-grid-box-dark")
            .data(Profit_Graph.timeLines)
            .enter()
            .append("rect")
            .filter(function (d) {
                // only draw elements that are an even number of increments from the start
                return ((d - Profit_Graph.adminStartTime) / (Profit_Graph.timeIncrement)) % 2 == 0;
            })
            .attr("x", function (d) {
               return Profit_Graph.mapTimeToXAxis(d);
            })
            .attr("y", 0)
            // width of a sinle timeIncrement should be 5 secs ?
            .attr("width", Profit_Graph.timeIncrement / Profit_Graph.timeInterval * (Profit_Graph.profitElementWidth - Profit_Graph.axisLabelWidth - Profit_Graph.graphPaddingRight))   
            .attr("height", Profit_Graph.profitElementHeight)
            .attr("class", "time-grid-box-dark");

         //Draw labels for time grid lines
         Profit_Graph.profitSVG.selectAll("text.time-grid-line-text")
            .data(Profit_Graph.timeLines)
            .enter()
            .append("text")
            .attr("text-anchor", "start")
            .attr("x", function (d) {
               return Profit_Graph.mapTimeToXAxis(d) + 5 ;
            })
            .attr("y", Profit_Graph.profitElementHeight - 5)
            .text(function (d) {
               return Profit_Graph.millisToTime(d);
            })
            .attr("class", "time-grid-line-text");
    }

    drawPriceGridLines(priceMapFunction) {

        Profit_Graph.profitSVG.selectAll("line.price-grid-line")
            .data(Profit_Graph.profitPriceLines)
            .enter()
            .append("line")
            .attr("x1", 0)
            .attr("x2", Profit_Graph.profitElementWidth - Profit_Graph.axisLabelWidth)        //changed 7/27/17
            .attr("y1", function (d) {
                return Profit_Graph.mapProfitPriceToYAxis(d);
            })
            .attr("y2", function (d) {
                return Profit_Graph.mapProfitPriceToYAxis(d);
            })
            .attr("class", function (d) {
                return d != 0 ? "price-grid-line" : "price-grid-line-zero";
        });
    }
    drawPriceAxis(){
        Profit_Graph.profitSVG.selectAll("text.price-grid-line-text")
            .data(Profit_Graph.profitPriceLines)
            .enter()
            .append("text")
            .attr("text-anchor", "start")
            .attr("x", Profit_Graph.profitElementWidth - Profit_Graph.axisLabelWidth + 12)  // << why this fuck is this 12
            .attr("y", function (d) {  
               return Profit_Graph.mapProfitPriceToYAxis(d) + 3;
            })
            .attr("class", "price-grid-line-text")
            .text(function (d) {
                return d * (1e-4);
        });
    }

    drawProfit(historyDataSet, profitJumps) {
       
        Profit_Graph.profitSVG.selectAll("line.my-profit-out line.my-profit-maker line.my-profit-snipe")
            .data(historyDataSet, function (d) {   
            // historyDataSet structure = [[startTime, endTime, startProfit, endProfit, state],...] 
               return d;
            })
            .enter()
            .append("line")
            .filter(function (d) {
               return d.endTime >= (Profit_Graph.currentTime - Profit_Graph.timeInterval);
            })
            .attr("x1", function (d) {
               return Profit_Graph.mapTimeToXAxis(d.startTime);
            })
            .attr("x2", function (d) {
               return Profit_Graph.mapTimeToXAxis(d.endTime);
            })
            .attr("y1", function (d) {
               return Profit_Graph.mapProfitPriceToYAxis(d.startProfit);
            })
            .attr("y2", function (d) {
               document.querySelector('info-table').setAttribute("profit",(d.endProfit*(1e-4)).toFixed(2)); 
               return Profit_Graph.mapProfitPriceToYAxis(d.endProfit);
            })
            .attr("class", function (d) {
               // a masterpiece // no fuck you // hey thats not nice
               return d.state == "OUT" ? "my-profit-out" : (d.state == "MAKER" ? "my-profit-maker" : "my-profit-snipe");
        });

        Profit_Graph.profitSVG.selectAll("line.positive-profit line.negative-profit")
            .data(profitJumps)      
            // profitJumps structure = {timestamp:(nano), newPrice:(thousands), oldPrice:(thousands)}    
            .enter()
            .append("line")
            .filter(function (d) {
               return d.timestamp >= (Profit_Graph.currentTime - Profit_Graph.timeInterval);
            })
            .attr("x1", function (d) {
               return Profit_Graph.mapTimeToXAxis(d.timestamp);
            })
            .attr("x2", function (d) {
               return Profit_Graph.mapTimeToXAxis(d.timestamp);
            })
            .attr("y1", function (d) {
               return Profit_Graph.mapProfitPriceToYAxis(d.oldProfit);     //old profit
            })
            .attr("y2", function (d) {
               return Profit_Graph.mapProfitPriceToYAxis(d.newProfit);     //current profit
            })
            .attr("class", function (d) {
                  return d.oldProfit < d.newProfit ? "my-positive-profit" : "my-negative-profit";
            });   
    }

    draw(){
        //Clear the svg elements
        Profit_Graph.profitSVG.selectAll("*").remove();
        // the current time relative to the backend of otree; graph.timeOffset during the transition
        // is 0, but eventually we will calculate per player what the delay over django channels is 

        Profit_Graph.currentTime =  Profit_Graph.getTime() - Profit_Graph.timeOffset; 
        Profit_Graph.timeSinceStart = Profit_Graph.currentTime - Profit_Graph.adminStartTime;
        // Print to console.log everytime a second occurs
        if((Profit_Graph.previousTime != Math.trunc(Profit_Graph.timeSinceStart / Profit_Graph.nanoToSec)) && Profit_Graph.debug["secondTick"]){
            Profit_Graph.previousTime = Math.trunc(Profit_Graph.timeSinceStart / Profit_Graph.nanoToSec);
        } 
        
        Profit_Graph.curTimeX = Profit_Graph.mapTimeToXAxis(Profit_Graph.currentTime);

        // recalculate market price bounds
        Profit_Graph.calcPriceBounds();

        // recalculate if virtual right side of graph is more than a graph.timeIncrement past last graph.timeLine line
        var rightSideOfGraph = Profit_Graph.timeLines[Profit_Graph.timeLines.length - 1] + Profit_Graph.timeIncrement;

        if (Profit_Graph.currentTime + Profit_Graph.advanceTimeShown > rightSideOfGraph){
            
            var startTime = Profit_Graph.currentTime - Profit_Graph.timeInterval;
            var endTime = Profit_Graph.currentTime + Profit_Graph.advanceTimeShown;
            Profit_Graph.timeLines = Profit_Graph.calcTimeGridLines(startTime, endTime, Profit_Graph.timeIncrement);
        } 
        //Invoke all of the draw functions
        Profit_Graph.drawTimeGridLines();
        Profit_Graph.drawPriceGridLines();
        Profit_Graph.drawPriceAxis();

        var speed = document.querySelector("input-section").shadowRoot.querySelector("#speed_checkbox").checked
        /* *****************************************************************************
        * Data Structures present in Redwood front end, and need to be adapted to otree 
        ******************************************************************************/ 

    // historyDataSet = [[startTime, endTime, startProfit, endProfit, state],...] 
    // 2-D array where each index contains a different portion of the profit line *over the entire experiment*
    // Each index has a startTime (nano), endTime (nano), startProfit (thousands), endProfit (thousands) 
    Profit_Graph.profitSegments[Profit_Graph.profitSegments.length - 1]["endTime"] = Profit_Graph.currentTime;
    
    var profitDecrement = 0;
    if(speed){
        profitDecrement = (Profit_Graph.profitSegments[Profit_Graph.profitSegments.length - 1]["endTime"] - Profit_Graph.profitSegments[Profit_Graph.profitSegments.length - 1]["startTime"]) * -(oTreeConstants.speed_cost);
    }


    Profit_Graph.profitSegments[Profit_Graph.profitSegments.length - 1]["endProfit"] = Profit_Graph.profitSegments[Profit_Graph.profitSegments.length - 1]["startProfit"] + profitDecrement;
    Profit_Graph.profit = Profit_Graph.profitSegments[Profit_Graph.profitSegments.length - 1]["startProfit"] + profitDecrement;

        Profit_Graph.drawProfit(Profit_Graph.profitSegments, Profit_Graph.profitJumps);
        if(oTreeConstants.end_msg == "off"){
            requestAnimationFrame(Profit_Graph.draw);
        } else {
            Profit_Graph.clear();
        }
    }

    clear(){
        //Clear the svg elements
        Profit_Graph.profitSVG.selectAll("*").remove();
    }

    init(startFP, startingWealth) {
        for(var i = 2; i < arguments.length; i++){
            Profit_Graph.debug[arguments[i]] = true;
        }
        Profit_Graph.previousTime = 0;
        // nanoseconds per picxel 
        Profit_Graph.nanosecondPerPixel = Profit_Graph.timeInterval / (Profit_Graph.profitElementWidth - Profit_Graph.axisLabelWidth - Profit_Graph.graphPaddingRight);   
        // the amount of nano taken up by the axisLabelWidth ad graphPadding riht
        Profit_Graph.advanceTimeShown = Profit_Graph.nanosecondPerPixel * (Profit_Graph.axisLabelWidth + Profit_Graph.graphPaddingRight);
        // collect an array of price values where the horizontal lines will be drawn
        Profit_Graph.profitPriceLines = Profit_Graph.calcPriceGridLines(Profit_Graph.maxPriceProfit, Profit_Graph.minPriceProfit, Profit_Graph.profitPriceGridIncrement);
        var endTime = Profit_Graph.adminStartTime + Profit_Graph.timeInterval + Profit_Graph.advanceTimeShown;
        Profit_Graph.timeLines = Profit_Graph.calcTimeGridLines(Profit_Graph.adminStartTime, endTime, Profit_Graph.timeIncrement);

    }
}

window.customElements.define('profit-graph', ProfitGraph);
