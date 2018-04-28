/*Patrick Toral ptoral@ucsc.edu*/
/*Front End Javascript for start.html*/
/*Handles the Button Logic and the Graph shown in start.html*/
var n = 10;
var data = d3.range(n).map(function(d) { return {"y": 0}});
Draw_Graph(data);
//alert("hi danb");

/*Starting Button Logic*/
document.getElementById("maker").onclick = function () {
  if ((document.getElementById("maker").className == "button-off") && (document.getElementById("sniper").className != "button-pressed")){
    $("#maker").toggleClass('button-off button-pressed');
    Button_Pressed("maker");
    //send the order if not button pressed (reduces the chance of double orders)
  }
  $("#out").attr('class', 'button-off');
  $("#sniper").attr('class', 'button-off');
};

    document.getElementById("sniper").onclick = function () {
        if ((document.getElementById("sniper").className == "button-off") && (document.getElementById("sniper").className != "button-pressed")){
            $("#sniper").toggleClass('button-off button-pressed');
            Button_Pressed("sniper");
            //send the order if not button pressed (reduces the chance of double orders)
        }
        $("#maker").attr('class', 'button-off');
        $("#out").attr('class', 'button-off');
    };

    document.getElementById("out").onclick = function () {
        if (document.getElementById("out").className == "button-off"){
            $("#out").toggleClass('button-off button-on');
            //send the out message
        }
        $("#maker").attr('class', 'button-off');
        $("#sniper").attr('class', 'button-off');
    };

var button_timer;
var graph_timer;

function Button_Pressed(id_name){
  //Wait .5 seconds until you can send a replace order
  button_timer = setTimeout(Button_Change.bind(null,id_name), 500);
}
function Button_Change(id_name){
  //Changing the class and color for the button to be pressed
  $("#"+id_name).toggleClass('button-pressed button-on');
}

function Draw_Graph(data){
  
  data.push({"y": d3.randomUniform(-1,1)()});
  data.shift();
  Make_Profit_Graph(10,data);
  graph_timer = setTimeout(Draw_Graph.bind(null,data), 10);
};
/*
function Change_Data(data){
  //Wait .5 seconds until you can send a replace order
  console.log(data);
  var other = data.shift();
  console.log(other);
  var new_element = {"y": d3.randomUniform(1)() };
  data.push(new_element);
  console.log(data);
};
*/
/*End Button Logic*/

/*Start Graphing*/
function Make_Profit_Graph(n,data){
  d3.select(".line").remove(); 
  // 2. Use the margin convention practice 
  var margin = {top: 50, right: 50, bottom: 50, left: 50}
    , width = window.innerWidth - margin.left - margin.right // Use the window's width 
    , height = window.innerHeight - margin.top - margin.bottom; // Use the window's height
  // The number of datapoints
  // 5. X scale will use the index of our data
  var xScale = d3.scaleLinear()
      .domain([0, n-1]) // input
      .range([0, width]); // output

  // 6. Y scale will use the randomly generate number 
  var yScale = d3.scaleLinear()
      .domain([-1, 1]) // Fundamental Price +-Spread  
      .range([height, 0]); // output

  //console.log(data[data.length - 1]);
  var class_flag
  if (data[data.length - 1] > data[data.length -2]){

  } else if (data[data.length - 1] < data[data.length -2]){

  }
  // 7. d3's line generator
  var line = d3.line()
      .x(function(d, i) { return xScale(i); }) // set the x values for the line generator
      .y(function(d) { return yScale(d.y); }) // set the y values for the line generator 
      .curve(d3.curveMonotoneX) // apply smoothing to the line

  // 1. Add the SVG to the page and employ #2
  var svg = d3.select("#profit-graph")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  // 4. Call the y axis in a group tag
  svg.append("g")
      .attr("class", "y axis")
      .call(d3.axisLeft(yScale)); // Create an axis component with d3.axisLeft

  // 9. Append the path, bind the data, and call the line generator 
  svg.append("path")
      .datum(data) // 10. Binds data to the line 
      .attr("class", "line") // Assign a class for styling 
      .attr("d", line); // 11. Calls the line generator 
}

/*
         var width = 400, height = 300;
         var data = [100, 120, 140, 160, 180, 200];
         var svg = d3.select("#profit-graph")
            .attr("width", width)
            .attr("height", height)
            .style("background-color","white");
         g = svg.append("g").attr("transform", "translate(" + 45 + "," + 150 + ")");
         
         var xscale = d3.scaleLinear()
            .domain([0, d3.max(data)])
            .range([0, width - 60]);
         
         var yscale = d3.scaleLinear()
            .domain([-d3.max(data), d3.max(data)])
            .range([height - 20, 0]);
    
         var x_axis = d3.axisBottom().scale(xscale);
         
         var y_axis = d3.axisLeft().scale(yscale);
         
         svg.append("g")
            .attr("transform", "translate(55, 10)")
            .call(y_axis);

        svg.append("g")
            .attr("transform", "translate(55, 282)")
            .call(x_axis);
        
        //var n = 40, random = d3.randomNormal(-200, 200), data = d3.range(30).map(random);
        console.log(data);

        g.append("text")
          .attr("class", "y-label")
          .attr("text-anchor", "end")
          .attr("x", -18)
          .attr("y", 0)
          .text("Profit");

        g.append("text")
          .attr("class", "y-label")
          .attr("text-anchor", "end")
          .attr("x", -20)
          .attr("y", 14)
          .text("in $");
                
        svg.append("path")
    .datum(data) // 10. Binds data to the line 
    .attr("class", "line") // Assign a class for styling 
    .attr("d", line); // 11. Calls the line generator 
    */
         
/*
    //n = max profit need toa add 
    var n = 40, random = d3.randomNormal(0, 1), data = d3.range(30).map(random);

    var svg = d3.select("#profit-graph"), margin = {top: 20, right: 20, bottom: 20, left: 40},
        width = +svg.attr("width") - margin.left - margin.right,
        height = +svg.attr("height") - margin.top - margin.bottom,
        style = svg.style("background-color","white"),
        g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var x = d3.scaleLinear()
        .domain([1, n - 2])
        .range([0, width]);

    var y = d3.scaleLinear()
        //domain is spread +- your current profit
        .domain([-20, 20])
        .range([height, 0]);

    var line = d3.line()
        .x(function(d, i) { return x(i); })
        .y(function(d, i) { return y(d); });

    g.append("text")
    .attr("class", "y-label")
    .attr("text-anchor", "end")
    .attr("x", 0)
    .attr("y", height/2)
    .text("Profit");

    g.append("defs").append("clipPath")
        .attr("id", "clip")
      .append("rect")
        .attr("width", width)
        .attr("height", height);

    g.append("g")
        .attr("class", "axis axis--y")
        .call(d3.axisLeft(y));

    g.append("g")
    .attr("clip-path", "url(#clip)")
      .append("path")
        .attr("stroke-width", "12")
        .datum(data)

      .transition()
        .duration(700)
        .ease(d3.easeLinear)
        .on("start", tick);

    function tick() {

      // Push a new data point onto the back.
      data.push(random());

      // Redraw the line.
      d3.select(this)
          .attr("d", line)
          .attr("transform", 20);

      // Slide it to the left.
      d3.active(this)
          .attr("transform", "translate(" + x(0) + ",0)")
        .transition()
          .on("start", tick);

      // Pop the old data point off the front.
      data.shift();

    }
*/
/*End Graphing*/
