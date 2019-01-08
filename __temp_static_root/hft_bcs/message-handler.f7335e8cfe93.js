//All socket actions are stored in this object to be used in the seperated js files
let socketActions = {};
console.log("test 1");
/*
Socket Actions
*/
    //Socket Connection
    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    var socket = new WebSocket(ws_scheme + '://' + window.location.host + "/hft/{{player.market}}/{{player.id}}/");
   
    socketActions.socket = socket;
 
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
         socketActions.socket.onmessage = function (event) {
             
            var fund_price = document.querySelector('info-table').fp;
            var obj = jQuery.parseJSON(event.data);
            var spread = document.querySelector("info-table").spread_value;

            /*
            * FPC message: NASDAQ pricing changes
            * Update FP on info-table
            * Update bid and ansk on info-table
            * Draw FPC based on the difference of the current FPC and the new FPC
            */
            if(obj.FPC != undefined){
                
            var FPCDollarAmount = (obj.FPC*(1e-4)).toFixed(2);
            document.querySelector('info-table').fp = FPCDollarAmount;
            var difference = Math.abs(fund_price - (obj.FPC/10000));     
            spreadGraph.updateBidAndAsk(FPCDollarAmount,spread);

            if((obj.FPC/10000) > fund_price){
                difference = difference*-1;
            }
            difference = difference*10000;

            // spreadGraph.drawFPC((difference == NaN) ? 0 : difference);
            for(var key in spreadGraph.spread_lines){
                for(var token in spreadGraph.spread_lines[key]){
                    spreadGraph.spread_lines[key][token] -= parseInt(difference);
                    spreadGraph.spread_lines[key][token] -= parseInt(difference);
                }
            }
            /*
            * Draw Execution on the spread-graph
            * Draw Execution on the profit-graph
            */
            }else if(obj.EXEC != undefined){
            var timeNow = profitGraph.getTime();
            var exec = {};
            exec["player"] = obj.EXEC.id;
            exec["side"] = obj.EXEC.token[4];
            exec["profit"] = obj.EXEC.profit;
            exec["orig_price"] = obj.EXEC.orig_price;


            spreadGraph.executionHandler(exec);

            if(obj.EXEC.id == otree.playerIDInGroup){   
                
                profitGraph.profitJumps.push(
                    {
                        timestamp:timeNow,
                        oldProfit:profitGraph.profit,
                        newProfit:profitGraph.profit + obj.EXEC.profit, 
                    }
                );

                profitGraph.profit += obj.EXEC.profit;
                profitGraph.profitSegments.push(
                    {
                        startTime:timeNow,
                        endTime:timeNow, 
                        startProfit:profitGraph.profit, 
                        endProfit:profitGraph.profit,
                        state:document.querySelector('info-table').player_role
                    }
                )   
            } 

            /*
            * Update spread_lines for CDA, spreadLinesFBAConcurrent for FBA
            * Remove maker spread if they left the market
            * Find smallest spread, if player is then spread bar blue green otherwise
            * Draw maker lines on the spread-graph as they come in for CDA not if FBA draw on batch processed obj.BATCH == "P"
            */
            }else if(obj.SPRCHG != undefined) {
            // Number.MAX_SAFE_INTEGER
            var player_id = parseInt(otree.playerIDInGroup);
            var smallest_spread = [-1,Infinity];

            for(var key in obj.SPRCHG){
                var incomingSpread = (obj.SPRCHG[key]["A"] - obj.SPRCHG[key]["B"])/10000;
                if(key == player_id && obj.SPRCHG[key] != 0 ){
                    spreadGraph.last_spread = incomingSpread;
                }
                delete spreadGraph.spread_lines[key];
                
                if(obj.SPRCHG[key] == 0){
                    console.log("Left the market");
                    // Maker has left the market so remove that maker tick
                    spreadGraph.spread_svg.selectAll(".others_line_top_" + key).remove();
                    spreadGraph.spread_svg.selectAll(".others_line_bottom_" + key).remove();
                    delete obj.SPRCHG[key];
                } 
                // process all new spreads  after the zeros have been removed
                if(incomingSpread < 0){
                    console.error("Invalid spread calculation from a SPRCHG msg", obj.SPRCHG);
                }

                if(incomingSpread < smallest_spread[1]){
                    smallest_spread[0] = parseInt(key);
                    smallest_spread[1] = incomingSpread;
                }
            }
            var lineParser = spreadGraph.spread_lines;

            for(var key in lineParser){
                // process all new spreads after the zeros have been removed
                var spread = (lineParser[key]["A"] - lineParser[key]["B"])/10000;
                if(spread < smallest_spread[1]){
                    smallest_spread[0] = parseInt(key);
                    smallest_spread[1] = spread;
                }
            }
            if(smallest_spread[0] == player_id){
                spreadGraph.smallest_spread = true;
            }else{
                spreadGraph.smallest_spread = false;
            }

            spreadGraph.drawSpreadChange(obj.SPRCHG);

            /*
            * Recieved on sync message sent from the backend, sent from backend when they recieved all player_ready
            * Start experiment (remove grey overlay)
            */
            }else if(obj.SYNC != undefined){
            console.log("Recieved SYNC");
            otree.sync = true; 
            startExperiment();

            /*
            * Recieved when number of trader enters or leaves the market, update the info-table accordingly
            */
            } else if(obj.TOTAL != undefined){

            // Player State Change message from the backend
            var total_makers = obj.TOTAL.MAKER;
            var total_snipers = obj.TOTAL.SNIPER;
            var total_out = obj.TOTAL.OUT;
            var total_traders = total_makers + total_snipers;
            document.querySelector("info-table").num_traders = total_traders;
            document.querySelector("info-table").num_makers = total_makers;

            } 
 
        };
    
        // Show a disconnected message when the WebSocket is closed.
        socketActions.socket.onclose = function (event) {
            console.log('disconnected from oTree');
        };    