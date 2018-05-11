
// /*Front End Javascript for start.html*/
// /*Handles the Button Logic and the Graph shown in start.html*/

//             var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
//             var socket = new WebSocket(ws_scheme + '://' + window.location.host + "/hft/{{group.id}}/{{player.id}}/");
//             console.log(ws_scheme + '://' + window.location.host + "/hft/{{group.id}}/{{player.id}}/");
//             // Handle any errors that occur.
//             socket.onerror = function (error) {
//                 console.log('WebSocket Error: ' + error);
//             };
//             $('#player_id').html({{player.id_in_group}})
//             $('#player_role').html('Out');
//             $('#curr_speed_cost').html(0);
//             var speed = false;
//             updatespeed = function () {
//                 speed = !speed;
//                 if(speed){
//                     $('#curr_speed_cost').html({{Constants.speed_cost}});
//                 }else {
//                     $('#curr_speed_cost').html(0);
//                 }
//                 var msg = {
//                     type: 'speed_change',
//                     id: {{player.id}},
//                     id_in_group: {{player.id_in_group}},
//                     speed: speed
//                 };
//                 if (socket.readyState === socket.OPEN) {
//                     socket.send(JSON.stringify(msg));
//                 }
//             }

//             // Show a connected message when the WebSocket is opened.
//             socket.onopen = function (event) {
//                 console.log('connected to oTree');
//             };
//             // Handle messages sent by the server.
//             socket.onmessage = function (event) {
//                 var obj = jQuery.parseJSON(event.data);
//                 role = obj.state;
//                 console.log('here');
//                 $('#player_role').html(role);
//             };
//             // Show a disconnected message when the WebSocket is closed.
//             socket.onclose = function (event) {
//                 console.log('disconnected from oTree');
//             };



// /*********************************
// START BUTTON LOGIC //may the force be with you
// *********************************/
//   //MAKER BUTTON
//   document.getElementById("maker").onclick = function () {
//     if ((document.getElementById("maker").className == "button-off") && (document.getElementById("maker").className != "button-pressed")){
//         //IF BUTTON IS NOT PRESSED OR ON THEN TURN IT ON AFTER DELAD (Button_Pressed())
//         $("#maker").toggleClass('button-off button-pressed');
//         var msg = {
//           type: 'role_change',
//           id: {{player.id}},
//           id_in_group: {{player.id_in_group}},
//           state: "MAKER"
//         };
//         if (socket.readyState === socket.OPEN) {
//           socket.send(JSON.stringify(msg));
//         }
//         console.log(msg);
//         Button_Pressed("maker");
//         //CHANGE TABLE VALUE
//         $('#player_role').html('Maker');

//         Spread_Graph.drawLine(2);
//         //send the order if not button pressed (reduces the chance of double orders)
//     }
//     //TURN THE REST OF THE BUTTONS OFF

//     $("#out").attr('class', 'button-off');
//     $("#sniper").attr('class', 'button-off');
//   };

//   //SNIPER BUTTON
//   document.getElementById("sniper").onclick = function () {
//       if ((document.getElementById("sniper").className == "button-off") && (document.getElementById("sniper").className != "button-pressed")){
//         //IF BUTTON IS NOT PRESSED OR ON THEN TURN IT ON AFTER DELAD (Button_Pressed())
//         $("#sniper").toggleClass('button-off button-pressed');
//         var msg = {
//           type: 'role_change',
//           id: {{player.id}},
//           id_in_group: {{player.id_in_group}},
//           state: "SNIPE"
//         };
//         if (socket.readyState === socket.OPEN) {
//           socket.send(JSON.stringify(msg));
//         }
//         console.log(msg);
//         Button_Pressed("sniper");
//         //send the order if not button pressed (reduces the chance of double orders)
//         //CHANGE TABLE VALUE
//         $('#player_role').html('Sniper');
//       }
//     //TURN THE REST OF THE BUTTONS OFF

//     Spread_Graph.clear();
//     $("#maker").attr('class', 'button-off');
//     $("#out").attr('class', 'button-off');
//   };

//   //OUT BUTTON
//   document.getElementById("out").onclick = function () {
//     if (document.getElementById("out").className == "button-off"){
//       //IF THE BUTTON IS OFF TURN IT ON WITH NO DELAY
//       $("#out").toggleClass('button-off button-on');
//       var msg = {
//         type: 'role_change',
//         id: {{player.id}},
//         id_in_group: {{player.id_in_group}},
//         state: "OUT"
//       };
//       if (socket.readyState === socket.OPEN) {
//         socket.send(JSON.stringify(msg));
//       }
//       //CHANGE TABLE VALUE
//       $('#player_role').html('Out');
//       console.log(msg);
//       //send the out message

//     }
//     Spread_Graph.clear();
//     //TURN THE REST OF THE BUTTONS OFF
//     $("#maker").attr('class', 'button-off');
//     $("#sniper").attr('class', 'button-off');
//   };

//   var button_timer;
//   var graph_timer;
//   function Button_Pressed(id_name){
//     //Wait .5 seconds for button pressed
//     button_timer = setTimeout(Button_Change.bind(null,id_name),500);
//   }
//   function Button_Change(id_name){
//     //TURNING BUTTON ON
//     $("#"+id_name).toggleClass('button-pressed button-on');
//   }

//   var button_timer;
//   var graph_timer;
//   function Button_Pressed(id_name){
//     //Wait  seconds until you can send a replace order
//     button_timer = setTimeout(Button_Change.bind(null,id_name), 500);
//   }
//   function Button_Change(id_name){
//     //Changing the class and color for the button to be pressed
//     $("#"+id_name).toggleClass('button-pressed button-on');
//   }
// /*********************************
// END BUTTON LOGIC
// *********************************/

// var Spread_Graph = {};
// var Profit_Graph = {};

// var n = 20; 
// var data = d3.range(17).map(function(d) { return  0}); //Testing Purposes
// max_spread = 10; // Pull from Constansts

// (function() {

//   var spread_width = $("#spread-graph").width(),
//       spread_height = $("#spread-graph").height(),
//       spread_svg = d3.select("#spread-graph")
//                   .attr("width", spread_width)
//                   .attr("height", spread_height);

//   function drawStartState(){
//     spread_line = spread_svg.append("svg:line")
//                    .attr("x1", spread_width/2)
//                    .attr("y1", 0)
//                    .attr("x2", spread_width/2)
//                    .attr("y2", spread_height)
//                    .style("stroke", "lightgrey")
//                    .style("stroke-width", 5);

//     spread_line_fundamental_price = spread_svg.append("svg:line")
//                    .attr("x1", spread_width - (spread_width - 45))
//                    .attr("y1", spread_height/2 - 90)
//                    .attr("x2", spread_width - 45)
//                    .attr("y2", spread_height/2 - 90)
//                    .style("stroke", "grey")
//                    .style("stroke-width", 5);

//   }

//   /***********************************************
//   DEALING WITH MOUSE CLICKS ON THE SPREAD GRAPHS
//   ************************************************/
//   function svgClickListener(){
//       spread_svg.on('click',function(d) { 
//         role = $("#player_role").text();
//         if(role == "Maker"){

//         //The dimensions the svg take up
//          spread_x = document.getElementById("spread-graph").getBoundingClientRect().x;
//          spread_y = document.getElementById("spread-graph").getBoundingClientRect().y;

//          //Where the grey middle line is
//          svg_middle_x = spread_width/2;
//          svg_middle_y = spread_height/2 - 90;

//         //The tuple in which the mouse is clicked within the svg 
//         spread_position = {x:(d3.event.clientX - spread_x),y:(d3.event.clientY - spread_y)};

//         //finding the distance from the mid
//         if(spread_position.y >= svg_middle_y){
//           distance_from_middle = spread_position.y - svg_middle_y;
//         } else {
//           distance_from_middle = svg_middle_y -spread_position.y ;
//         }
//         //Ratio between the distance and the mid
//         ratio = svg_middle_y / distance_from_middle;

//         //Spread is the ratio except in dollars which is what the actual spread is
//         money_ratio = max_spread/ratio;
//         my_spread = money_ratio.toFixed(2);
//         //alert("mouse position in svg when clicked is " + "(" + spread_position.x+ "," +spread_position.y +") and max spread is " + spread);
//         //alert("This is your spread +-$"+actual_spread);
        

//       var msg = {
//         type: 'spread_change',
//         id: {{player.id}},
//         id_in_group: {{player.id_in_group}},
//         spread: "state_out"
//       };
//       if (socket.readyState === socket.OPEN) {
//         socket.send(JSON.stringify(msg));
//       }
//       console.log(msg);


//         $("#spread_number").text('+-$'+my_spread);
//         //Time to draw the lasers tat go into the spread graph
//         drawSpreadLine(my_spread);
//         }
//       });
//   }

//   function drawSpreadLine(my_spread){
//        d3.selectAll(".my_line").remove();
//        d3.selectAll("rect").remove();
//        spread_y = document.getElementById("spread-graph").getBoundingClientRect().y;
//        //Where the grey middle line is
//        svg_middle_y = spread_height/2 - 90;

//        money_ratio =  max_spread/my_spread;
//        y_coordinate = svg_middle_y/money_ratio;
//        console.log(y_coordinate);
//       //Ratio between the distance and the mid
      

//     your_spread_line_top = spread_svg.append("svg:line")
//                .attr("x1", spread_width - 35)
//                .attr("y1", svg_middle_y - y_coordinate)
//                .attr("x2", spread_width)
//                .attr("y2", svg_middle_y - y_coordinate)
//                .attr("class","my_line");

//     your_spread_line_bottom = spread_svg.append("svg:line")
//                .attr("x1", spread_width - 35)
//                .attr("y1", y_coordinate + svg_middle_y)
//                .attr("x2", spread_width)
//                .attr("y2", y_coordinate + svg_middle_y)
//                .attr("class","my_line");
//     //WAIT FOR SPEED AND THEN SET THE SPREAD with the bar line

//       addLineAnimation();
      
//       setTimeout(function(d){
//         drawSpreadBar(my_spread,svg_middle_y,y_coordinate);
//       }, 500);
      
//       //Timeout is whether or not speed is on
//   }

//   function addLineAnimation(){
//     //SETTING THE SPREAD TO THE LINE
//     spread_lines = d3.selectAll(".my_line");
//     add_animation = spread_lines
//                     .transition()
//                     // duration is whether or not speed is on
//                     .duration(500)
//                     .attr("x1", 85)
//                     .attr("x2", spread_width - 85);         
//   }

//   function drawSpreadBar(my_spread,svg_middle_y,y_coordinate){
//     //take into account
//     var bar_color = "";
    
//     //if not other maker within the spread
//     bar_color = "green_bar";
//     your_bar_rect = spread_svg.append("svg:rect")
//                .attr("x", spread_width - (spread_width - 85))
//                .attr("y", svg_middle_y - y_coordinate)
//                .attr("width", spread_width - 170)
//                .attr("height", 2*y_coordinate)
//                .attr("class",bar_color);
//   }

//   function clearGraph(){
//     d3.selectAll(".my_line").remove();
//     d3.selectAll("rect").remove();
//   }

//   Spread_Graph.start = drawStartState;
//   Spread_Graph.drawLine = drawSpreadLine;
//   Spread_Graph.animateLine = addLineAnimation;
//   Spread_Graph.drawBar = drawSpreadBar;
//   Spread_Graph.listen = svgClickListener;
//   Spread_Graph.clear = clearGraph;
// }());




// (function(){
//   var profit_width = $("#profit-graph").width()// Use the window's width 
//     , profit_height = $("#profit-graph").height()  // Use the window's height
//     ,x_axis_min = 0
//     ,x_axis_max = n-1;

//   var xScale = d3.scaleLinear()
//       .domain([x_axis_min, x_axis_max]) // input
//       .range([0, profit_width - 30]) // output
//     , yScale = d3.scaleLinear()
//       .domain([ - max_spread, max_spread]) // Fundamental Price +-Spread  
//       .range([profit_height - 180 ,5]); // output

//   var line = d3.line()
//       .x(function(d, i) { return xScale(i); }) // set the x values for the line generator
//       .y(function(d) { return yScale(d); }) // set the y values for the line generator 
//       .curve(d3.curveMonotoneX)// apply smoothing to the line
  
//   var svg = d3.select("#profit-graph")
//       .attr("width", profit_width)
//       .attr("height", profit_height)
//       .append("g")
//       .attr("transform", "translate(0,0)");

//   function graphStartState(){
//     svg.append("path")
//       .datum(data)
//       .attr("class", "line") 
//       .attr("d", line); 


//     svg.append("g")
//         .attr("class", "y_axis")
//         .attr("transform", "translate(" + (profit_width - 28) + ",0)")
//         .call(d3.axisRight(yScale));

//     svg.append("g")
//         .attr("class", "x_axis")
//         .attr("transform", "translate(0," + (profit_height - 180) + ")")
//         .call(d3.axisTop(d3.scaleLinear()
//         .domain([0, 17]) //Timeeeee!!!!
//         .range([0, profit_width - 30])));


//     setInterval(function() {
//        Update();  
//     }, 500);
//   }

//   function Update(){
//     //Remove Previous Graph Bounds
//     d3.select(".y_axis").remove();
//     d3.select(".x_axis").remove();

//     //Get Time From Timer
//     x_axis_min++;
//     x_axis_max++;

//     //Get A new value and put into the array
//     var profit = 2;
//     data.shift(); // remove the first element of the array
//     data.push(d3.randomUniform(-5,5)() ); 
//     //alert(y_data);
//     //Redraw the line add in transition
//     svg.select("path")
//     .datum(data) 
//     .attr("d", line)
//     .attr("transform", "translate(" + xScale(1) + ")")
//     .transition()
//     .duration(500)
//     .ease(d3.easeLinear)
//     .attr("transform", "translate(" + xScale(0) + ")");

//     //Redraw the y axis with new bounds
//     svg.append("g")
//       .attr("class", "y_axis")
//       .attr("transform", "translate(" + (profit_width - 28) + ",0)")
//       .call(d3.axisRight(d3.scaleLinear()
//       .domain([-10,10]) // Fundamental Price +- Spread  
//       .range([profit_height-180,5]))) // Create an axis component with d3.axisLeft

//     //Redraw the x axis with new bounds
//     svg.append("g")
//       .attr("class", "x_axis")
//       .attr("transform", "translate(0," + (profit_height - 180) + ")")
//       .call(d3.axisTop(d3.scaleLinear()
//       .domain([x_axis_min, x_axis_max]) //Timeeeee!!!!
//       .range([0, profit_width - 30])))
//   }
  
//   Profit_Graph.start = graphStartState;
//   Profit_Graph.update = Update;

// }());

// Spread_Graph.start();
// Spread_Graph.listen();
// Profit_Graph.start();