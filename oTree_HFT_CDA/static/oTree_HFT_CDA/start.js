alert("This is the start before module");
var oTreeHighFrequencyTrading = angular.module('oTreeHighFrequencyTrading', []);


oTreeHighFrequencyTrading.controller("HFTStartController",
   ["$scope",
      '$interval', //Completely Remove not in use
       "oTreeSubject",
      "DataHistory",
      "Graphing",
      "$http",
      function ($scope, $interval, rs, dataHistory, graphing, $http) {
        alert("This is the start after module within the function youre good!");

         var CLOCK_FREQUENCY = 50;   // Frequency of loop, measured in ms delay between ticks

         $scope.sliderVal = 0;
         $scope.state = "state_out";
         $scope.using_speed = false;
         $scope.spread = 0;
         $scope.maxSpread = 1;
         $scope.lastTime = 0;
         $scope.mousePressed = false;
         $scope.oldOffsetY = null;
         $scope.curOffsetY = null;
         $scope.startTime = 0;
         $scope.jumpOffsetY = 0;
         $scope.LaserSound;
         $scope.statename = "Out";
         $scope.minSpread = .01;
        $scope.inputData;
        $scope.adminStartTime;

         $scope.s = {
            NO_LINES: 0,
            DRAW_FIRST: 1,
            FIRST_DRAWN: 2,
            OUT: 4
         };

         $scope.e = {
            NO_EVENT: 0,
            JUMP: 1,
            CLICK: 2,
            FIRST_TIME: 3
         };
         $scope.lastEvent = $scope.e.NO_EVENT;
         $scope.event = $scope.e.NO_EVENT;
         $scope.tickState = $scope.s.NO_LINES;

         //Loops at speed CLOCK_FREQUENCY in Hz, updates the graph
         $scope.update = function (timestamp) {
            $scope.FSM($scope.tickState, $scope.event, timestamp);
            $scope.FPCpoll();
            $scope.BatchPoll();

            $scope.tradingGraph.draw($scope.dHistory);

            if ($scope.using_speed) {
               $scope.dHistory.profit -= (getTime() - $scope.lastTime) * $scope.dHistory.speedCost / 1000000000; //from cda
            }
            $scope.lastTime = getTime();

            $scope.dHistory.CalculatePlayerInfo();
            requestAnimationFrame($scope.update);
            $scope.$digest();                      //for updating profit
         };

         // Sorts a message list with the lowest actionTime first
         $scope.sortMsgList = function (msgList) {
            msgList.sort(function (a, b) {
               if (a.actionTime < b.actionTime)
                  return -1;
               if (a.actionTime > b.actionTime)
                  return 1;
               return 0;
            });
         };

         // Sends a message to the Market Algorithm
         $scope.sendToMarketAlg = function (msg, delay) {
            if (delay == 0) {
               if ($scope.isDebug) {
                  $scope.logger.logSend(msg, "Market Algorithm");
               }
               $scope.mAlgorithm.recvMessage(msg);
               //$scope.dHistory.recvMessage(msg);
            }
            else {
               var packedMsg = packMsg(msg, delay);
               if ($scope.isDebug) {
                  $scope.logger.logSendWait(packedMsg.msg);
               }
               $scope.sendWaitListToMarketAlg.push(packedMsg);
               $scope.sortMsgList($scope.sendWaitListToMarketAlg);
            }
         };

         // Sends a message to the Group Manager
         $scope.sendToGroupManager = function (msg, delay) {
            if ($scope.isDebug) {
               $scope.logger.logSend(msg, "Group Manager");
            }
            rs.send("To_Group_Manager", msg);
         };

         //First function to run when page is loaded
          //player.on_load in oTree???
         rs.on_load(function () {
            //rs.send("set_player_time_offset", Date.now());
            rs.send("set_player_time_offset", getTime());
            rs.send("Subject_Ready");
         });

         //Initializes experiment

         rs.recv("Experiment_Begin", function (uid, data) {
            $scope.groupNum = data.groupNumber;
            $scope.group = data.group;
            $scope.period = data.period;

            $scope.maxSpread = data.maxSpread;
            $scope.sliderVal = $scope.maxSpread / 2;
            $scope.spread = $scope.maxSpread / 2;
            $scope.exchangeRate = data.exchangeRate;


            // create associative array to go from uid to local group id for display purposes
            $scope.displayId = {};
            for (var index = 0; index < data.group.length; index++) {
               $scope.displayId[data.group[index]] = index + 1;
            }

            //Create the logger for this start.js page
            $scope.isDebug = data.isDebug;
            if ($scope.isDebug) {
               $("#ui").append('<div class="terminal-wrap"><div class="terminal-head">Subject Message Log</div><div id="subject-log" class="terminal"></div></div>');
               $scope.logger = new MessageLogger("Subject Manager " + String(rs.user_id), "yellow", "subject-log");
            }

            //Create data history and graph objects
            $scope.dHistory = dataHistory.createDataHistory(data.startTime, data.startFP, rs.user_id, $scope.group, $scope.isDebug, data.speedCost, data.startingWealth, data.maxSpread, data.batchLength);
            $scope.dHistory.init();
            $scope.tradingGraph = graphing.makeTradingGraph("market_graph", "profit_graph", data.startTime, data.playerTimeOffsets[rs.user_id], data.batchLength, "timer_graph");
            $scope.tradingGraph.init(data.startFP, data.maxSpread, data.startingWealth);

            //load the audio objects
            $scope.AudioInit();
            // set last time and start looping the update function
            $scope.lastTime = getTime();
            //$interval($scope.update, CLOCK_FREQUENCY);
            requestAnimationFrame($scope.update);
            $scope.adminStartTime = data.startTime;
            if (data.input_arrays.length > 0) {
               $scope.inputData = data.input_arrays[parseInt(rs.user_id)];           //save user's input array
               var delay = $scope.inputData[0][0];             //time til first input action
               var timeSinceStart = $scope.getTimeSinceStart();              //time (in ms) since the experiment began
               window.setTimeout($scope.processInputAction, delay - timeSinceStart, 0);
            }

            // if input data was provided, setup automatic input system
            
         });

         rs.recv("From_Group_Manager", function (uid, msg) {
            handleMsgFromGM(msg);
         });

         $scope.getTimeSinceStart = function () {
            return (getTime() - $scope.adminStartTime) / 1000000;
         };

         $scope.GetStateName = function (){
            if ($scope.state == "state_maker") return "Maker";
            if ($scope.state == "state_out") return "Out";
            if ($scope.state == "state_snipe") return "Sniper";
         };

         $scope.GetSpread = function (){
            if($scope.state == "state_maker") return $scope.spread;
            else return "N/A";
         };

         $scope.AudioInit = function (){
            $scope.LaserSound = new Audio("/static/experiments/redwood-high-frequency-trading-remote/Sounds/laser1.wav");
            $scope.LaserSound.volume = .1;
            // $scope.LaserSound.play();
         };

         $scope.setSpeed = function (value) {
            if (value !== $scope.using_speed) {
               $scope.using_speed = value;
               var msg = new Message("USER", "USPEED", [rs.user_id, $scope.using_speed, getTime()]);
               $scope.sendToGroupManager(msg);           //still have to send to market algorithm to update player state
               
            }
         };

         $("#speed-switch")
            .click(function () {
               $scope.setSpeed(this.checked);
            });

         $scope.BatchPoll = function() {
            if($scope.dHistory.startBatch){
               $scope.dHistory.startBatch = false;
               // $scope.startTimer();
               $scope.tradingGraph.BatchSVG.selectAll("*").remove();    //restart the batch progress bar
               $scope.tradingGraph.BatchStart();
               $scope.tradingGraph.BatchProgress();
            }
         };   
         
         $scope.startTimer = function() {
            $('#timer').pietimer({
                timerSeconds: 3,
                color: 'SkyBlue',
                fill: false,
                showPercentage: false,
                callback: function() {
                    $('#timer').pietimer('reset');
                    $('#timer').pietimer('start');
                }
            });
         };
   

         $scope.FPCpoll = function () {
            if($scope.event != $scope.e.JUMP){
               if($scope.tradingGraph.oldFundPrice != $scope.dHistory.curFundPrice[1]){
                  $scope.event = $scope.e.JUMP;
                  $scope.jumpOffsetY = $scope.tradingGraph.FPCswing;
               }
            }
         }; 

         $scope.CalculateYPOS = function (offset) {
            //reflects my current spread choice over the center of svg element
            return $scope.tradingGraph.elementHeight - offset;
         };


         $scope.FSM = function (state, event, timestamp) {
            switch(state){ 
               case $scope.s.NO_LINES:
                  switch(event){ 
                     case $scope.e.CLICK:                                                       //user's first click on the graph
                        $scope.startTime = window.performance.now();                            //set start time for the lasers
                        $scope.tradingGraph.callDrawSpreadTick($scope.curOffsetY, $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);                        //generate the top line
                        $scope.tradingGraph.callDrawSpreadTick($scope.CalculateYPOS($scope.curOffsetY), $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);  //generate the bottom line
                        $scope.lastEvent = $scope.e.FIRST_TIME;                                 //special case
                        $scope.event = $scope.e.NO_EVENT;                                       //clear event
                        $scope.tickState = $scope.s.DRAW_FIRST;                                 //transition to DRAW_FIRST
                        break;

                     case $scope.e.JUMP:
                        $scope.event = $scope.e.NO_EVENT;                                       //clear the event, we don't care about jumps at this time
                        break;

                     default:
                        // console.log("pay jason more");
                        break;
                  }
                  break;
               case $scope.s.DRAW_FIRST:
                  switch(event){
                     case $scope.e.CLICK:                                                       //user clicked before the lines were fully drawn
                        $scope.startTime = window.performance.now();                            //reset start time for the new lines
                        $scope.tradingGraph.marketSVG.selectAll("#current").remove();           //replace moving lines with your new spread
                        // $scope.tradingGraph.marketSVG.selectAll("#box").remove();               //clear old spread region if it's been drawn
                        $scope.tradingGraph.callDrawSpreadTick($scope.curOffsetY, $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);                       //new top line at new spread
                        $scope.tradingGraph.callDrawSpreadTick($scope.CalculateYPOS($scope.curOffsetY), $scope.using_speed, timestamp - $scope.startTime, false, "current", 0); //new bot line at new spread
                        // $scope.tradingGraph.DrawBox($scope.tradingGraph, $scope.oldOffsetY, $scope.jumpOffsetY, $scope.CalculateYPOS($scope.oldOffsetY), "box");                                 //display your spread region at your old spread
                        $scope.lastEvent = $scope.event;                                        //keep track of the last event
                        $scope.event = $scope.e.NO_EVENT;                                       //clear event
                        $scope.tickState = $scope.s.DRAW_FIRST;                                 //transition to default case

                     case $scope.e.JUMP:
                        $scope.startTime = window.performance.now();                            //reset start time for the new lines
                        $scope.tradingGraph.marketSVG.selectAll("#current").remove();           //moving spread lines will be replaced
                        // $scope.tradingGraph.marketSVG.selectAll("#box").remove();               //clear old spread region for shifted one
                        $scope.tradingGraph.callDrawSpreadTick($scope.curOffsetY, $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);                        //send new top line at new spread
                        $scope.tradingGraph.callDrawSpreadTick($scope.CalculateYPOS($scope.curOffsetY), $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);  //send new bot line at new spread
                        $scope.oldOffsetY = $scope.curOffsetY;                                  //must set this so upon leaving this case so it will be correct in default
                        // $scope.tradingGraph.DrawBox($scope.tradingGraph, $scope.oldOffsetY, $scope.jumpOffsetY, $scope.CalculateYPOS($scope.oldOffsetY), "box"); //shift the spread region by the jump distance
                        $scope.lastEvent = $scope.event;                                        //keep track of the last event
                        $scope.event = $scope.e.NO_EVENT;                                       //clear event, transition to default
                        // $scope.LaserSound.play();
                        break;

                     default:                                                                   //no event, so continue drawing the lines
                        if($scope.using_speed){
                           if(timestamp - $scope.startTime < $scope.tradingGraph.fastDelay){    //current spread lines havent reached the end
                              $scope.tradingGraph.marketSVG.selectAll("#current").remove();     //delete line history so they appear moving
                              $scope.tradingGraph.callDrawSpreadTick($scope.curOffsetY, $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);                        //current top line
                              $scope.tradingGraph.callDrawSpreadTick($scope.CalculateYPOS($scope.curOffsetY), $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);  //current bot line
                              if($scope.lastEvent != $scope.e.FIRST_TIME){                      //don't want to display spread region until the first lines reach the center
                                 // $scope.tradingGraph.marketSVG.selectAll("#box").remove();      //clear redundant spread regions for performance
                                 // $scope.tradingGraph.DrawBox($scope.tradingGraph, $scope.oldOffsetY, $scope.jumpOffsetY, $scope.CalculateYPOS($scope.oldOffsetY), "box");          //display your current spread region with offset if any
                              }
                           }
                           else{
                              $scope.oldOffsetY = $scope.curOffsetY;                            //both lines caught up, so they have the same offsets
                              $scope.jumpOffsetY = 0;                                           //safely move back the spread region to the current spread
                              $scope.tickState = $scope.s.FIRST_DRAWN;                          //the lines drawn without an interruption -> transition to FIRST_DRAWN
                           }  
                        }
                        else {                                                                  //no event, so continue drawing the lines
                           if(timestamp - $scope.startTime < $scope.tradingGraph.slowDelay){    //current spread lines havent reached the end
                              $scope.tradingGraph.marketSVG.selectAll("#current").remove();     //delete line history so they appear moving
                              $scope.tradingGraph.callDrawSpreadTick($scope.curOffsetY, $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);                        //current top line
                              $scope.tradingGraph.callDrawSpreadTick($scope.CalculateYPOS($scope.curOffsetY), $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);  //current bot line
                              if($scope.lastEvent != $scope.e.FIRST_TIME){                      //don't want to display spread region until the first lines reach the center
                                 // $scope.tradingGraph.marketSVG.selectAll("#box").remove();      //clear redundant spread regions for performance
                                 // $scope.tradingGraph.DrawBox($scope.tradingGraph, $scope.oldOffsetY, $scope.jumpOffsetY, $scope.CalculateYPOS($scope.oldOffsetY), "box");          //display your current spread region
                              } 
                           }
                           else{
                              $scope.oldOffsetY = $scope.curOffsetY;                            //both lines caught up, so they have the same offset
                              $scope.jumpOffsetY = 0;                                           //safely move back the spread region to the current spread
                              $scope.tickState = $scope.s.FIRST_DRAWN;                          //the lines drawn without an interruption -> transition to FIRST_DRAWN
                           }
                        }
                        
                        break;
                  }
                  break;
               case $scope.s.FIRST_DRAWN:
                  switch(event){
                     case $scope.e.CLICK:                                                       //user clicked after lines reached the center point
                        $scope.startTime = window.performance.now();                            //reset start time for the new spread lines
                        $scope.tradingGraph.marketSVG.selectAll("#current").remove();           //remove static lines current spread
                        // $scope.tradingGraph.marketSVG.selectAll("#box").remove();               //remove current spread region for performance and safety
                        $scope.tradingGraph.callDrawSpreadTick($scope.curOffsetY, $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);                        //new top line at spread
                        $scope.tradingGraph.callDrawSpreadTick($scope.CalculateYPOS($scope.curOffsetY), $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);  //new bot line at spread
                        // $scope.tradingGraph.DrawBox($scope.tradingGraph, $scope.oldOffsetY, $scope.jumpOffsetY, $scope.CalculateYPOS($scope.oldOffsetY), "box");                                  //display your current spread region            
                        $scope.lastEvent = $scope.event;                                        //keep track of the last event
                        $scope.event = $scope.e.NO_EVENT;                                       //clear event
                        $scope.tickState = $scope.s.DRAW_FIRST;                                 //transition to DRAW_FIRST 
                        break;

                     case $scope.e.JUMP:
                        $scope.startTime = window.performance.now();                            //reset start time for the new lines
                        $scope.tradingGraph.marketSVG.selectAll("#current").remove();           //remove your current static lines
                        // $scope.tradingGraph.marketSVG.selectAll("#box").remove();               //remove your spread region
                        $scope.tradingGraph.callDrawSpreadTick($scope.curOffsetY, $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);                                 //new top line at current spread
                        $scope.tradingGraph.callDrawSpreadTick($scope.CalculateYPOS($scope.curOffsetY), $scope.using_speed, timestamp - $scope.startTime, false, "current", 0);           //new bot line at current spread
                        $scope.oldOffsetY = $scope.curOffsetY;                                  //must set this so upon leaving this case, it will work in default
                        // $scope.tradingGraph.DrawBox($scope.tradingGraph, $scope.oldOffsetY, $scope.jumpOffsetY, $scope.CalculateYPOS($scope.oldOffsetY), "box"); //display new shifted spread region
                        $scope.lastEvent = $scope.event;                                        //keep track of the last event
                        $scope.event = $scope.e.NO_EVENT;                                       //clear event
                        $scope.tickState = $scope.s.DRAW_FIRST;                                 //transition to DRAW_FIRST
                        // $scope.LaserSound.play();
                        break;

                     default:                                                                   //continue to draw static current spread until the next event
                        $scope.tradingGraph.marketSVG.selectAll("#current").remove();           //clear static 
                        // $scope.tradingGraph.marketSVG.selectAll("#box").remove();               //clear old spread region displays for performance
                        // $scope.tradingGraph.DrawBox($scope.tradingGraph, $scope.oldOffsetY, $scope.jumpOffsetY, $scope.CalculateYPOS($scope.oldOffsetY), "box");        //draw my current spread region
                        break;
                  }
                  break;

               case $scope.s.OUT:
                  switch(event){
                     case $scope.e.FIRST_TIME:
                        if(!$scope.using_speed){
                           window.setTimeout(function(){                                              //wait your delay before removing
                              $scope.tradingGraph.marketSVG.selectAll("#current").remove();           //clear any graph elements
                              // $scope.tradingGraph.marketSVG.selectAll("#box").remove();               //clear any graph elements
                           }, 500);
                        }
                        else{
                           $scope.tradingGraph.marketSVG.selectAll("#current").remove();           //clear any graph elements
                           // $scope.tradingGraph.marketSVG.selectAll("#box").remove();               //clear any graph elements
                        }
                        $scope.jumpOffsetY = 0;                                                 //reset variable
                        $scope.oldOffsetY = $scope.curOffsetY;                                  //reset variable
                        $scope.lastEvent = $scope.e.NO_EVENT;                                   //reset variable
                        $scope.event = $scope.e.NO_EVENT;                                       //clear the event
                        break;

                     case $scope.e.CLICK:
                        $scope.tickState = $scope.s.NO_LINES;                                   //only transition from out on a click or from UI buttons
                        //leave the event to be handled in NO_LINES
                        break;

                     default:
                        //Do nothing until user re enters the market
                        break;
                  }
                  break;
               }
         };


         $("#market_graph")
            .mousedown( function(event) {
               //only allow mousePressed to register after 
               $scope.mousePressed = true;                                       //set the flag so in case we leave the svg element we know it was a press
            })
            .mouseleave( function(event) {
               if ($scope.mousePressed) {                                        //only set the spread if svg has been clicked on
                  $scope.mousePressed = false;                                   //reset the flag
                  if (event.offsetY <= $scope.tradingGraph.elementHeight / 2) {      //you left the svg right of the center tick
                     $scope.spread = ($scope.maxSpread - Math.abs(2 * $scope.maxSpread * event.offsetY / $scope.tradingGraph.elementHeight)).toPrecision(2); //.1 increments
                     if($scope.spread > $scope.maxSpread) $scope.spread = $scope.maxSpread;                                       //cap max spread to 5
                     if($scope.spread <= $scope.minSpread) $scope.spread = $scope.minSpread;
                  } 
                  else {                                                            //you clicked below of the center tick
                     $scope.spread = (((2 * $scope.maxSpread * event.offsetY - $scope.tradingGraph.elementHeight / $scope.maxSpread) / $scope.tradingGraph.elementHeight) - $scope.maxSpread - .2).toPrecision(2); //.1 increments
                     if($scope.spread > $scope.maxSpread) $scope.spread = $scope.maxSpread;                                       //cap max spread to 5
                     if($scope.spread <= $scope.minSpread) $scope.spread = $scope.minSpread;
                 }
                  var msg = new Message("USER", "UUSPR", [rs.user_id, $scope.spread, getTime()]);
                  $scope.sendToGroupManager(msg);
                  var msg2 = new Message("USER", "UMAKER", [rs.user_id, getTime()]);
                  $scope.sendToGroupManager(msg2);

                  if ($scope.state != "state_maker") {
                     $scope.setState("state_maker");
                  }

                  $scope.tradingGraph.currSpreadTick = event.offsetY;            //sets the location to be graphed
                  $scope.oldOffsetY = $scope.curOffsetY;                                //update our last y position for receding lines
                  $scope.curOffsetY = event.offsetY;                             //set event to be handled in FSM
                  $scope.event = $scope.e.CLICK;

                  $scope.LaserSound.play();
               }
            })
            .mouseup( function(event) {
               if($scope.mousePressed){
                  $scope.mousePressed = false;                                      //reset the flag
                  if (event.offsetY <= $scope.tradingGraph.elementHeight / 2) {      //you clicked right of the center tick
                     $scope.spread = ($scope.maxSpread - Math.abs(2 * $scope.maxSpread * event.offsetY / $scope.tradingGraph.elementHeight)).toPrecision(2); //.1 increments
                     if($scope.spread > $scope.maxSpread) $scope.spread = $scope.maxSpread;                                       //cap max spread to 5
                     if($scope.spread <= $scope.minSpread) $scope.spread = $scope.minSpread;
                  }
                  else {                                                            //you clicked left of the center tick
                     $scope.spread = (((2 * $scope.maxSpread * event.offsetY - $scope.tradingGraph.elementHeight / $scope.maxSpread) / $scope.tradingGraph.elementHeight) - $scope.maxSpread - .2).toPrecision(2); //.1 increments
                     if($scope.spread > $scope.maxSpread) $scope.spread = $scope.maxSpread;                                       //cap max spread to 5
                     if($scope.spread <= $scope.minSpread) $scope.spread = $scope.minSpread;
                  }
                  var msg = new Message("USER", "UUSPR", [rs.user_id, $scope.spread, getTime()]);
                  $scope.sendToGroupManager(msg);
                  var msg2 = new Message("USER", "UMAKER", [rs.user_id, getTime()]);
                  $scope.sendToGroupManager(msg2);

                  if ($scope.state != "state_maker") {
                     $scope.setState("state_maker");
                  }

                  $scope.tradingGraph.currSpreadTick = event.offsetY;               //sets the location to be graphed
                  $scope.oldOffsetY = $scope.curOffsetY;                                   //update our last y position for receding lines
                  $scope.curOffsetY = event.offsetY;                                //set event to be handled in FSM
                  $scope.event = $scope.e.CLICK;

                  $scope.LaserSound.play();
               }
            });


         // button for setting state to sniper
         $("#state_snipe")
            .addClass("state-not-selected")
            .button()
            .click(function (event) {
               var msg = new Message("USER", "USNIPE", [rs.user_id, getTime()]);
               $scope.sendToGroupManager(msg);
               $scope.setState("state_snipe");
               $scope.tickState = $scope.s.OUT;
               $scope.event = $scope.e.FIRST_TIME;
            });

         // button for setting state to market maker
         $("#state_maker")
            .addClass("state-not-selected")
            .button()
            .click(function (event) {
               $scope.setState("state_maker");
               $scope.tickState = $scope.s.NO_LINES;        //fake a click event
               $scope.event = $scope.e.CLICK;
               $scope.curOffsetY = $scope.tradingGraph.elementHeight / 4;
               $scope.spread = $scope.maxSpread / 2;
               $scope.oldOffsetY = null;
               var nMsg = new Message("USER", "UUSPR", [rs.user_id, $scope.spread, getTime()]);
               $scope.sendToGroupManager(nMsg);
               var msg = new Message("USER", "UMAKER", [rs.user_id, getTime()]);
               $scope.sendToGroupManager(msg);
            });

         // button for setting state to "out of market"
         $("#state_out")
            .addClass("state-selected")
            .button()
            .click(function (event) {
               $scope.setSpeed(false);
               $("#speed-switch").prop("checked", false);

               var msg = new Message("USER", "UOUT", [rs.user_id, getTime()]);
               $scope.sendToGroupManager(msg);
               $scope.setState("state_out");
               $scope.tickState = $scope.s.OUT;
               $scope.event = $scope.e.FIRST_TIME;
            });

         $("#expand-graph")
            .button()
            .click(function () {
               $scope.tradingGraph.setExpandedGraph();
            });

         $("#contract-graph")
            .button()
            .click(function () {
               $scope.tradingGraph.setContractedGraph();
            });

         $("#market-zoom-in")
            .click(function () {
               $scope.tradingGraph.zoomMarket(true);
            });

         $("#market-zoom-out")
            .click(function () {
               $scope.tradingGraph.zoomMarket(false);
            });

         $("#profit-zoom-in")
            .click(function () {
               $scope.tradingGraph.zoomProfit(true);
            });

         $("#profit-zoom-out")
            .click(function () {
               $scope.tradingGraph.zoomProfit(false);
            });

         $scope.setState = function (newState) {
            $("#" + $scope.state).removeClass("state-selected").addClass("state-not-selected");
            $scope.state = newState;
            $("#" + $scope.state).removeClass("state-not-selected").addClass("state-selected");
         };

         // receive message from market algorithm to the data history object
         rs.recv("To_Data_History_" + String(rs.user_id), function (uid, msg) {
            if ($scope.isDebug) {
               $scope.logger.logRecv(msg, "Market Algorithm");
            }
            if ($scope.dHistory === undefined) return;
            $scope.dHistory.recvMessage(msg);
         });

         // receives message sent to all dataHistories
         rs.recv("To_All_Data_Histories", function (uid, msg) {
            if ($scope.isDebug) {
               $scope.logger.logRecv(msg, "Market Algorithm");
            }
            if ($scope.dHistory === undefined) return;
            $scope.dHistory.recvMessage(msg);
         });

         rs.recv("end_game", function (uid, msg) {
            console.log("ending game");
            rs.finish();
         });

         rs.recv("_next_period", function (uid, msg) {
            // console.log("Starting Next Period");
            rs.trigger("_next_period");
         });

         $scope.processInputAction = function (inputIndex) {
            if (inputIndex >= $scope.inputData.length - 1) return;
            //delay
            var delay = $scope.inputData[inputIndex + 1][0];      //time of the next input action
            var timeSinceStart = $scope.getTimeSinceStart();              //time (in ms) since the experiment began
            window.setTimeout($scope.processInputAction, delay - timeSinceStart, inputIndex + 1);

            switch ($scope.inputData[inputIndex][1]) {
               case "OUT":
                  var msg = new Message("USER", "UOUT", [rs.user_id, getTime()]);
                  $scope.sendToGroupManager(msg);
                  $scope.setState("state_out");

                  $scope.setSpeed(false);
                  $("#speed-switch").prop("checked", false);
                  $scope.tickState = $scope.s.OUT;
                  $scope.event = $scope.e.FIRST_TIME;
                  break;

               case "SNIPE":
                   var msg = new Message("USER", "USNIPE", [rs.user_id, getTime()]);
                  $scope.sendToGroupManager(msg);
                  $scope.setState("state_snipe");

                  $scope.tickState = $scope.s.OUT;
                  $scope.event = $scope.e.FIRST_TIME;
                  break;

               case "MAKER":
        if($scope.state != "state_maker") {
         $scope.setState("state_maker");
        }
                  console.log($scope.state, rs.user_id);
                  $scope.tickState = $scope.s.NO_LINES;        //fake a click event
                  $scope.event = $scope.e.CLICK;
                  $scope.curOffsetY = $scope.tradingGraph.elementHeight / 4;
                  $scope.spread = $scope.maxSpread / 2;
                  $scope.oldOffsetY = null;
                  var nMsg = new Message("USER", "UUSPR", [rs.user_id, $scope.spread, getTime()]);
                  $scope.sendToGroupManager(nMsg);

        var msg = new Message("USER", "UMAKER", [rs.user_id, getTime()]);
                  $scope.sendToGroupManager(msg);
                  break;

               case "FAST":
                  $scope.setSpeed(true);
                  $("#speed-switch").prop("checked", true);
                  break;

               case "SLOW":
                  $scope.setSpeed(false);
                  $("#speed-switch").prop("checked", false);
                  break;

               case "SPREAD":
                  $scope.spread = parseFloat($scope.inputData[inputIndex][2]);
                  var msg = new Message("USER", "UUSPR", [rs.user_id, $scope.spread, getTime()]);
                  $scope.sendToGroupManager(msg);

        var msg2 = new Message("USER", "UMAKER", [rs.user_id, getTime()]);
                  $scope.sendToGroupManager(msg2);

        if ($scope.state != "state_maker") {
                     $scope.setState("state_maker");
                  }
                  break;

               default:
                  console.error("invalid input: " + $scope.inputData[inputIndex][1]);
            }
         }
      }]);
