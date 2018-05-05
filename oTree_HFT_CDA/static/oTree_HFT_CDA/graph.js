/*Front End Javascript for start.html*/
/*Handles the Button Logic and the Graph shown in start.html*/

var n = 20; 
var data = d3.range(17).map(function(d) { return {"y": 0}});
spread = 3;

makeProfitGraph(n,0,data);
makeSpreadGraph(spread);

function makeSpreadGraph(spread){
  var spread_width = d3.select("#spread-graph").width() ;
  var spread_height = d3.select("#spread-graph").height() ;
  alert();
  d3.select("#spread-line")
      .attr('d','M 10 25  L 10 75  L 10 25  L 60 75')
      .attr('stroke', 'red')
      .attr('stroke-width', '2')
      .attr('fill','none');
}

function makeProfitGraph(n,x_data,y_data){

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
      .domain([ - 3, 3]) // Fundamental Price +-Spread  
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



graphStartState();

setInterval(function() {
         Update();  
      }, 500);

  function graphStartState(){
    svg.append("path")
    .datum(y_data)
    .attr("class", "line") 
    .attr("d", line); 

      // 4. Call the y axis in a group tag
  svg.append("g")
      .attr("class", "y_axis")
      .attr("transform", "translate(" + (width - 28) + ",0)")
      .call(d3.axisRight(yScale)); // Create an axis component with d3.axisLeft

svg.append("g")
      .attr("class", "x_axis")
      .attr("transform", "translate(0," + (height - 180) + ")")
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
      .attr("transform", "translate(" + (width - 28) + ",0)")
      .call(d3.axisRight(d3.scaleLinear()
      .domain([-3,3]) // Fundamental Price +- Spread  
      .range([height-180,5]))) // Create an axis component with d3.axisLeft

    //Redraw the x axis with new bounds
    svg.append("g")
      .attr("class", "x_axis")
      .attr("transform", "translate(0," + (height - 180) + ")")
      .call(d3.axisTop(d3.scaleLinear()
      .domain([x_axis_min, x_axis_max]) //Timeeeee!!!!
      .range([0, width - 30])))
  }
  
}

