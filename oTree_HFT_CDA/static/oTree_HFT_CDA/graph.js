/*Front End Javascript for start.html*/
/*Handles the Button Logic and the Graph shown in start.html*/

var n = 20; 
var data = d3.range(17).map(function(d) { return {"y": 0}});
spread = 10;

makeGraphs(n,0,data);

function makeGraphs(n,x_data,y_data){

  var margin = {top: 0, right: 0, bottom: 0, left: 0}
    , width = $("#profit-graph").width()// Use the window's width 
    , height = $("#profit-graph").height() ; // Use the window's height
  console.log(width);
  var x_axis_min = 0;
  var x_axis_max = n-1;

  var xScale = d3.scaleLinear()
      .domain([x_axis_min, x_axis_max]) // input
      .range([0, width - 30]); // output

  // 6. Y scale will use the randomly generate number 
  var yScale = d3.scaleLinear()
      .domain([ - 10, 10]) // Fundamental Price +-Spread  
      .range([height - 180 ,5]); // output

  // 7. d3's line generator
  var line = d3.line()
      .x(function(d, i) { return xScale(i); }) // set the x values for the line generator
      .y(function(d) { return yScale(d.y); }) // set the y values for the line generator 
      .curve(d3.curveMonotoneX)// apply smoothing to the line

  // 1. Add the SVG to the page and employ #2
  var svg = d3.select("#profit-graph")
      .attr("width", width)
      .attr("height", height)
    .append("g")
      .attr("transform", "translate(0,0)");

  var spread_width = $("#spread-graph").width(),
      spread_height = $("#spread-graph").height(),
      spread_svg = d3.select("#spread-graph")
                  .attr("width", spread_width)
                  .attr("height", spread_height);

graphStartState();


setInterval(function() {
         Update();  
}, 500);

  function graphStartState(){

  svg.append("path")
    .datum(y_data)
    .attr("class", "line") 
    .attr("d", line); 


  svg.append("g")
      .attr("class", "y_axis")
      .attr("transform", "translate(" + (width - 28) + ",0)")
      .call(d3.axisRight(yScale));

  svg.append("g")
      .attr("class", "x_axis")
      .attr("transform", "translate(0," + (height - 180) + ")")
      .call(d3.axisTop(d3.scaleLinear()
      .domain([0, 1]) //Timeeeee!!!!
      .range([0, width - 30])));

  spread_line = spread_svg.append("svg:line")
               .attr("x1", spread_width/2)
               .attr("y1", 0)
               .attr("x2", spread_width/2)
               .attr("y2", spread_height)
               .style("stroke", "lightgrey")
               .style("stroke-width", 5);

  spread_line_fundamental_price = spread_svg.append("svg:line")
               .attr("x1", spread_width - (spread_width - 45))
               .attr("y1", spread_height/2 - 90)
               .attr("x2", spread_width - 45)
               .attr("y2", spread_height/2 - 90)
               .style("stroke", "grey")
               .style("stroke-width", 5);
  }

  
   function Update(){
    //Remove Previous Graph Bounds
    d3.select(".y_axis").remove();
    d3.select(".x_axis").remove();

    //Get Time From Timer
    x_axis_min++;
    x_axis_max++;

    //Get A new value and put into the array
    var profit = 2;
    y_data.shift(); // remove the first element of the array
    y_data.push({"y": d3.randomUniform(-5,5)() } ); 

    //Redraw the line add in transition
    svg.select(".line")
    .data([y_data]) 
    .attr("d", line)
    .attr("transform", null)
    .transition()
    .duration(500)
    .ease(d3.easeLinear)
    .attr("transform", "translate(" + -1 + ")");

  //  .attr("transform", null)
  // .transition()
  //   

    //Redraw the y axis with new bounds
    svg.append("g")
      .attr("class", "y_axis")
      .attr("transform", "translate(" + (width - 28) + ",0)")
      .call(d3.axisRight(d3.scaleLinear()
      .domain([-10,10]) // Fundamental Price +- Spread  
      .range([height-180,5]))) // Create an axis component with d3.axisLeft

    //Redraw the x axis with new bounds
    svg.append("g")
      .attr("class", "x_axis")
      .attr("transform", "translate(0," + (height - 180) + ")")
      .call(d3.axisTop(d3.scaleLinear()
      .domain([x_axis_min, x_axis_max]) //Timeeeee!!!!
      .range([0, width - 30])))
  }


  /***********************************************
  DEALING WITH MOUSE CLICKS ON THE SPREAD GRAPHS
  ************************************************/
  spread_svg.on('click',function(d) { 
      role = $("#player_role").text();
      if(role == "Maker"){

      //The dimensions the svg take up
       spread_x = document.getElementById("spread-graph").getBoundingClientRect().x;
       spread_y = document.getElementById("spread-graph").getBoundingClientRect().y;

       //Where the grey middle line is
       svg_middle_x = spread_width/2;
       svg_middle_y = spread_height/2 - 90;

      //The tuple in which the mouse is clicked within the svg 
      spread_position = {x:(d3.event.clientX - spread_x),y:(d3.event.clientY - spread_y)};

      //finding the distance from the mid
      if(spread_position.y >= svg_middle_y){
        distance_from_middle = spread_position.y - svg_middle_y;
      } else {
        distance_from_middle = svg_middle_y -spread_position.y ;
      }
      //Ratio between the distance and the mid
      ratio = svg_middle_y / distance_from_middle;

      //Spread is the ratio except in dollars which is what the actual spread is
      money_ratio = spread/ratio;
      my_spread = money_ratio.toFixed(2);
      //alert("mouse position in svg when clicked is " + "(" + spread_position.x+ "," +spread_position.y +") and max spread is " + spread);
      //alert("This is your spread +-$"+actual_spread);
      
      $("#spread_number").text('+-$'+my_spread);
      //Time to draw the lasers tat go into the spread graph
      drawSpreadLine(my_spread);
    }
  });

  function drawSpreadLine(my_spread){
       d3.selectAll(".my_line").remove();
       d3.selectAll("rect").remove();
       spread_y = document.getElementById("spread-graph").getBoundingClientRect().y;
       //Where the grey middle line is
       svg_middle_y = spread_height/2 - 90;

       money_ratio =  spread/my_spread;
       y_coordinate = svg_middle_y/money_ratio;
       console.log(y_coordinate);
      //Ratio between the distance and the mid
      

    your_spread_line_top = spread_svg.append("svg:line")
               .attr("x1", spread_width - 35)
               .attr("y1", svg_middle_y - y_coordinate)
               .attr("x2", spread_width)
               .attr("y2", svg_middle_y - y_coordinate)
               .attr("class","my_line");

    your_spread_line_bottom = spread_svg.append("svg:line")
               .attr("x1", spread_width - 35)
               .attr("y1", y_coordinate + svg_middle_y)
               .attr("x2", spread_width)
               .attr("y2", y_coordinate + svg_middle_y)
               .attr("class","my_line");
    //WAIT FOR SPEED AND THEN SET THE SPREAD with the bar line

      addLineAnimation();
      
      setTimeout(function(d){
        drawSpreadBar(my_spread,svg_middle_y,y_coordinate);
      }, 300);
      
      //Timeout is whether or not speed is on
  }

  function addLineAnimation(){
    //SETTING THE SPREAD TO THE LINE
    spread_lines = d3.selectAll(".my_line");
    add_animation = spread_lines
                    .transition()
                    // duration is whether or not speed is on
                    .duration(300)
                    .attr("x1", 85)
                    .attr("x2", spread_width - 85);         
  }

  function drawSpreadBar(my_spread,svg_middle_y,y_coordinate){
    //take into account
    var bar_color = "";
    
    //if not other maker within the spread
    bar_color = "green_bar";
    your_bar_rect = spread_svg.append("svg:rect")
               .attr("x", spread_width - (spread_width - 85))
               .attr("y", svg_middle_y - y_coordinate)
               .attr("width", spread_width - 170)
               .attr("height", 2*y_coordinate)
               .attr("class",bar_color);
  }










  
}

