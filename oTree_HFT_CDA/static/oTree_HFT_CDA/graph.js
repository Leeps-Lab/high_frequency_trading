/*Front End Javascript for start.html*/
/*Handles the Button Logic and the Graph shown in start.html*/

/******************************************************
START BUTTON LOGIC 
******************************************************/

// document.getElementById("maker").onclick = function () {
//   if ((document.getElementById("maker").className == "button-off") && (document.getElementById("sniper").className != "button-pressed")){
//       $("#maker").toggleClass('button-off button-pressed');
//     //   var msg = {
//     //     type: 'role_change',
//     //     id: {{player.id}},
//     //     id_in_group: {{player.id_in_group}},
//     //     state: "state_maker"
//     //   };
//     // if (socket.readyState === socket.OPEN) {
//     //   socket.send(JSON.stringify(msg));
//     // }
//     Button_Pressed("maker");
//     //send the order if not button pressed (reduces the chance of double orders)
//   }
//   $("#out").attr('class', 'button-off');
//   $("#sniper").attr('class', 'button-off');
// };

//     document.getElementById("sniper").onclick = function () {
//         if ((document.getElementById("sniper").className == "button-off") && (document.getElementById("sniper").className != "button-pressed")){
//             $("#sniper").toggleClass('button-off button-pressed');
//           //   var msg = {
//           //     type: 'role_change',
//           //     id: {{player.id}},
//           //     id_in_group: {{player.id_in_group}},
//           //     state: "state_snipe"
//           //   };
//           // if (socket.readyState === socket.OPEN) {
//           //   socket.send(JSON.stringify(msg));
//           // }
//             Button_Pressed("sniper");
//             //send the order if not button pressed (reduces the chance of double orders)
//         }
//         $("#maker").attr('class', 'button-off');
//         $("#out").attr('class', 'button-off');
//     };

//     document.getElementById("out").onclick = function () {
//         if (document.getElementById("out").className == "button-off"){
//             $("#out").toggleClass('button-off button-on');
//           //   var msg = {
//           //     type: 'role_change',
//           //     id: {{player.id}},
//           //     id_in_group: {{player.id_in_group}},
//           //     state: "state_out"
//           //   };
//           // if (socket.readyState === socket.OPEN) {
//           //   socket.send(JSON.stringify(msg));
//           // }
//           Button_Pressed("out");
//             //send the out message
//         }
//         $("#maker").attr('class', 'button-off');
//         $("#sniper").attr('class', 'button-off');
//     };

// var button_timer;
// var graph_timer;

// function Button_Pressed(id_name){
//   //Wait  seconds until you can send a replace order
//   button_timer = setTimeout(Button_Change.bind(null,id_name), 500);
// }
// function Button_Change(id_name){
//   //Changing the class and color for the button to be pressed
//   $("#"+id_name).toggleClass('button-pressed button-on');
// }

/******************************************************
END BUTTON LOGIC 
******************************************************/


var n = 20;
var data = d3.range(16).map(function(d) { return {"y": 0}});
spread = 3;

Make_Profit_Graph(n,0,data);
Make_Spread_Graph(spread);

function Make_Spread_Graph(spread){
  var spread_width = d3.select("#spread-graph").width() ;
  var spread_height = d3.select("#spread-graph").height() ;
  alert();
  d3.select("#spread-line")
      .attr('d','M 10 25  L 10 75  L 10 25  L 60 75')
      .attr('stroke', 'red')
      .attr('stroke-width', '2')
      .attr('fill','none');
}

function Make_Profit_Graph(n,x_data,y_data){

  var margin = {top: 50, right: 50, bottom: 50, left: 50}
    , width = 495 // Use the window's width 
    , height = 450 ; // Use the window's height

  var x_axis_min = 0;
  var x_axis_max = n-1;

  var xScale = d3.scaleLinear()
      .domain([x_axis_min, x_axis_max]) // input
      .range([-40, width]); // output

  // 6. Y scale will use the randomly generate number 
  var yScale = d3.scaleLinear()
      .domain([ - 3, 3]) // Fundamental Price +-Spread  
      .range([height, - 40]); // output

  // 7. d3's line generator
  var line = d3.line()
      .x(function(d, i) { return xScale(i); }) // set the x values for the line generator
      .y(function(d) { return yScale(d.y); }) // set the y values for the line generator 
      .curve(d3.curveMonotoneX)// apply smoothing to the line

  // 1. Add the SVG to the page and employ #2
  var svg = d3.select("#profit-graph")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");



Graph_Start_State();

setInterval(function() {
         Update();  
      }, 500);

  function Graph_Start_State(){
    svg.append("path")
    .datum(y_data)
    .attr("class", "line") 
    .attr("d", line); 

      // 4. Call the y axis in a group tag
  svg.append("g")
      .attr("class", "y_axis")
      .attr("transform", "translate(" + width + ",0)")
      .call(d3.axisRight(yScale)); // Create an axis component with d3.axisLeft

svg.append("g")
      .attr("class", "x_axis")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisTop(xScale));
  }


  function Update() {
    //Remove Previous Graph Bounds
    d3.select(".y_axis").remove();
    d3.select(".x_axis").remove();

    //Get Time From Timer
    x_axis_min++;
    x_axis_max++;

    //Get A new value and put into the array
    var new_value = d3.randomUniform(-1,1)();
    y_data.shift(); // remove the first element of the array
    y_data.push({"y": new_value } ); 

    //Redraw the line add in transition
    svg.select(".line")
    .data([y_data]) 
    .attr("d", line)

    //Redraw the y axis with new bounds
    svg.append("g")
      .attr("class", "y_axis")
      .attr("transform", "translate(" + width + ",0)")
      .call(d3.axisRight(d3.scaleLinear()
      .domain([-3,3]) // Fundamental Price +- Spread  
      .range([height, - 40]))) // Create an axis component with d3.axisLeft

    //Redraw the x axis with new bounds
    svg.append("g")
      .attr("class", "x_axis")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisTop(d3.scaleLinear()
      .domain([x_axis_min, x_axis_max]) //Timeeeee!!!!
      .range([-40, width - 5])))
  }
  
}

