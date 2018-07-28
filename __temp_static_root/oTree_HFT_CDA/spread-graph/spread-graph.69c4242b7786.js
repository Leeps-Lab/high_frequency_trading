import {html, PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';
/**
 * @customElement
 * @polymer
 */
class SpreadGraph extends PolymerElement {
  constructor() {
    super();
    //First we access the shadow dom object were working with
    Spread_Graph.spread_graph_shadow_dom = document.querySelector("spread-graph").shadowRoot;
    //Second we add the HTML neccessary to be manipulated in the constructor and the subsequent functions
    Spread_Graph.spread_graph_shadow_dom.innerHTML = `
      <style>
.line {
    stroke: steelblue;
    stroke-width: 3.5px;
    fill: none;
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

.others_line{
  stroke:rgb(2, 3, 4);
  stroke-width:2px;
}

.green_bar{
  fill:#6edd68;
  opacity: 0.1;
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
      <svg id="spread-graph"></svg>
    `;

  /*  Spread Constant Information 
     *   oTreeConstants.max_spread = {{Constants.max_spread}}; 
     *   oTreeConstants.default_spread = {{Constants.default_spread}};
     *   oTreeConstants.smallest_spread = {{Constants.smallest_spread}};

     *   Initialize all the values needed for the spread graph and draw the start state
  */
     
    // Spread_Graph.spread_width and Spread_Graph.spread_height
    // this.spread_width  = Graph_Features.spread_width;
    // this.spread_height = Graph_Features.spread_height;

    //Getting the Shadow DOM variable to be able to use to be selected by d3
    Spread_Graph.spread_svg_dom = Spread_Graph.spread_graph_shadow_dom.querySelector("#spread-graph");
    Spread_Graph.spread_svg_dom.style.width = Spread_Graph.spread_width;
    Spread_Graph.spread_svg_dom.style.height = Spread_Graph.spread_height;

    //d3 Selection of the SVG we will be using this variable from now on
    Spread_Graph.spread_svg = d3.select(Spread_Graph.spread_svg_dom);
    
    /*
      Functions attached to the Spread_Graph object
    */

    Spread_Graph.start = this.start;
    Spread_Graph.dis = true;
    //Onclick listener . . .  of course
    Spread_Graph.listen = this.listen;
    Spread_Graph.sendSpreadChange = this.sendSpreadChange;
    Spread_Graph.drawMySpreadLines = this.drawMySpreadLines;
    Spread_Graph.clear = this.clear;
    Spread_Graph.addOthersLineAnimation = this.addOthersLineAnimation;
    Spread_Graph.drawTransactionBar = this.drawTransactionBar;    
    Spread_Graph.drawSpreadBar = this.drawSpreadBar;
    Spread_Graph.updateSmallest = this.updateSmallest;

    //Creating the start state
    Spread_Graph.start();
    //Activating the event listener
    Spread_Graph.listen();

  }
  start(){
    /*Drawing the start state when the window opens*/
    var spread_line = Spread_Graph.spread_svg.append("svg:line")
                       .attr("x1", Spread_Graph.spread_width/2)
                       .attr("y1", 0)
                       .attr("x2", Spread_Graph.spread_width/2)
                       .attr("y2", Spread_Graph.spread_height)
                       .style("stroke", "lightgrey")
                       .style("stroke-width", 5);

    var spread_line_fundamental_price = Spread_Graph.spread_svg.append("svg:line")
                       .attr("x1", 60)
                       .attr("y1", Spread_Graph.spread_height/2 )
                       .attr("x2", Spread_Graph.spread_width - 60)
                       .attr("y2", Spread_Graph.spread_height/2)
                       .style("stroke", "grey")
                       .style("stroke-width", 3);
  }

  listen(){
    Spread_Graph.spread_svg.on('click',function(d) { 
      var role = document.querySelector('info-table').player_role;
        if(role == "MAKER"){
          var spread_x = Spread_Graph.spread_x;
          var spread_y = Spread_Graph.spread_y;
          var svg_middle_x = Spread_Graph.spread_width / 2;
          var fp_line_y = Spread_Graph.spread_height / 2;

          var clicked_point = {
            x:(d3.event.clientX - spread_x),
            y:(d3.event.clientY - spread_y)
          };
 
          var distance_from_middle = Math.abs(clicked_point.y - fp_line_y);
          
          var ratio = distance_from_middle / (Spread_Graph.spread_height/2);

          var my_spread = (ratio*oTreeConstants.max_spread).toFixed(0);
          console.log(my_spread);
          Spread_Graph.sendSpreadChange(my_spread);
          } else if(role == "OUT"){
             //  //Send in default order for maker
             // document.querySelector('input-section').shadowRoot.querySelector("#maker").click();
            //IF BUTTON IS NOT PRESSED OR ON THEN TURN IT ON AFTER DELAD (Button_Pressed())
                    document.querySelector("input-section").shadowRoot.querySelector("#maker").className = "button-pressed";

                    document.querySelector("info-table").player_role = "Maker";

                    var timeNow = Profit_Graph.getTime() - Profit_Graph.timeOffset;
                    Profit_Graph.profitSegments.push(
                        {
                            startTime:timeNow,
                            endTime:timeNow, 
                            startProfit:Profit_Graph.profit, 
                            endProfit:Profit_Graph.profit,
                            state:document.querySelector("info-table").player_role
                        }
                    );

                    var msg = {
                        type: 'role_change',
                        id: oTreeConstants.player_id,
                        id_in_group: oTreeConstants.player_id_in_group,
                        state: "MAKER"
                    };

                    if (socketActions.socket.readyState === socketActions.socket.OPEN) {
                        socketActions.socket.send(JSON.stringify(msg));
                    }
                            var button_timer = setTimeout(document.querySelector("input-section").shadowRoot.querySelector("#maker").className = "button-on",500);


                    document.querySelector("input-section").shadowRoot.querySelector("#sniper").className = "button-off";
                    document.querySelector("input-section").shadowRoot.querySelector("#out").className = "button-off";

                    //Where the grey middle line is
                    var svg_middle_x = Spread_Graph.spread_width / 2;
                    var fp_line_y = Spread_Graph.spread_height / 2;

                    //The tuple in which the mouse is clicked within the svg 
                    click_point = {
                        x:(d3.event.clientX - Spread_Graph.spread_x),
                        y:(d3.event.clientY - Spread_Graph.spread_y)
                    };

                    //finding the distance from the mid
                    distance_from_middle = Math.abs(click_point.y - fp_line_y);

                    ratio = distance_from_middle / (Spread_Graph.spread_height / 2);

                    my_spread = (ratio * oTreeConstants.max_spread).toFixed(0);

                    Spread_Graph.sendSpreadChange(my_spread);
                }
    });
  }

  sendSpreadChange(my_spread = oTreeConstants.default_spread){
      var msg = {
                type: 'spread_change',
                id: oTreeConstants.player_id ,
                id_in_group: oTreeConstants.player_id_in_group,
                spread: my_spread
            };
            if (socketActions.socket.readyState === socketActions.socket.OPEN) {
                socketActions.socket.send(JSON.stringify(msg));
            }
            // console.log(msg);
            document.querySelector('info-table').setAttribute('spread_value','+-' + (my_spread / 1000).toFixed(2));
  }

  drawMySpreadLines(newLines={}, offset=0, exec={}, inv=false){
    var exec_side = "";
    var exec_spread = "";
    var player_id = oTreeConstants.player_id_in_group;
   
    for(var key in Spread_Graph.spread_lines){
      if(key==player_id){
        var svg_middle_y = Spread_Graph.spread_height/2;
        var my_spread = parseInt(Spread_Graph.spread_lines[key]["A"] - Spread_Graph.spread_lines[key]["B"]);
        var money_ratio =  oTreeConstants.max_spread/my_spread;
        var y_coordinate = svg_middle_y/money_ratio;
        var lines = []
        if(exec.player != key || exec.side != "S"){
          your_spread_line_top = Spread_Graph.spread_svg.append("svg:line")
              .attr("x1", (Spread_Graph.spread_width / 2) - 25)
              .attr("y1", svg_middle_y - y_coordinate + offset)
              .attr("x2", (Spread_Graph.spread_width / 2) + 25)
              .attr("y2", svg_middle_y - y_coordinate + offset)
              .attr("stroke-width",3)
              .attr("class","my_line");
              
          lines.push(your_spread_line_top);
        }else if(exec.player == key && exec.side == "S"){
            exec_side = "S";
            exec_spread = my_spread;
        }

        if(exec.player != key || exec.side != "B"){          
            your_spread_line_bottom = Spread_Graph.spread_svg.append("svg:line")
                .attr("x1", (Spread_Graph.spread_width / 2) - 25)
                .attr("y1", y_coordinate + svg_middle_y + offset)
                .attr("x2", (Spread_Graph.spread_width / 2) + 25)
                .attr("y2", y_coordinate + svg_middle_y + offset)
                .attr("stroke-width",3)
                .attr("class","my_line");
            lines.push(your_spread_line_bottom);
        }else if(exec.player == key && exec.side == "B"){
            exec_side = "B";
            exec_spread = my_spread;
        }
        Spread_Graph.addOthersLineAnimation(lines, 0);
        Spread_Graph.drawSpreadBar(my_spread,svg_middle_y,y_coordinate, offset, key);
        if(exec_side != ""){
            Spread_Graph.drawTransactionBar(exec_spread, svg_middle_y,y_coordinate, exec_side,((exec.profit > 0) ? "transaction_bar_light_green" : "transaction_bar_light_red"));
        }
      } else {
        var lines = [];
        //Where the grey middle line is
        var svg_middle_y = Spread_Graph.spread_height/2;
        my_spread = parseInt(Spread_Graph.spread_lines[key]["A"] - Spread_Graph.spread_lines[key]["B"]);
        money_ratio =  oTreeConstants.max_spread/my_spread;
        y_coordinate = svg_middle_y/money_ratio;
        // console.log(y_coordinate);
        //Ratio between the distance and the mid
        if(exec.player != key || exec.side != "S"){
            your_spread_line_top = Spread_Graph.spread_svg.append("svg:line")
                .attr("x1", (Spread_Graph.spread_width / 2) - 15)
                .attr("y1", svg_middle_y - y_coordinate + offset)
                .attr("x2", (Spread_Graph.spread_width / 2) + 15)
                .attr("y2", svg_middle_y - y_coordinate + offset)
                .attr("stroke-width",1)
                .attr("class","others_line");
            lines.push(your_spread_line_top);
        }else if(exec.player == key && exec.side == "S"){
            exec_side = "S";
            exec_spread = my_spread;
        }
        if(exec.player != key || exec.side != "B"){
            your_spread_line_bottom = Spread_Graph.spread_svg.append("svg:line")
                .attr("x1", (Spread_Graph.spread_width / 2) - 15)
                .attr("y1", y_coordinate + svg_middle_y + offset)
                .attr("x2", (Spread_Graph.spread_width / 2) + 15)
                .attr("y2", y_coordinate + svg_middle_y + offset)
                .attr("stroke-width",1)
                .attr("class","others_line");
            lines.push(your_spread_line_bottom);
        }else if(exec.player == key && exec.side == "B"){
            exec_side = "B";
            exec_spread = my_spread;
        }
        Spread_Graph.addOthersLineAnimation(lines, 0);
        if(exec_side != ""){
            Spread_Graph.drawTransactionBar(my_spread,svg_middle_y,y_coordinate,exec_side, ((exec.profit > 0) ? "transaction_bar_dark_green" : "transaction_bar_dark_red"));
        }
      }
    }

    for(var key in newLines){
                if(key == oTreeConstants.player_id_in_group){
                    //Where the grey middle line is
                    svg_middle_y = Spread_Graph.spread_height / 2;
                    
                    my_spread = parseInt(newLines[key]["A"] - newLines[key]["B"]);
                    money_ratio =  oTreeConstants.max_spread/my_spread;
                    y_coordinate = svg_middle_y/money_ratio;
                    // console.log(y_coordinate);
                    //Ratio between the distance and the mid
                    var your_spread_line_top = Spread_Graph.spread_svg.append("svg:line")
                        .attr("x1", Spread_Graph.spread_width)
                        .attr("y1", svg_middle_y - y_coordinate + offset)
                        .attr("x2", Spread_Graph.spread_width - 25)
                        .attr("y2", svg_middle_y - y_coordinate + offset)
                        .attr("stroke-width",3)
                        .attr("class","my_line");
                
                    var your_spread_line_bottom = Spread_Graph.spread_svg.append("svg:line")
                        .attr("x1", Spread_Graph.spread_width)
                        .attr("y1", y_coordinate + svg_middle_y + offset)
                        .attr("x2", Spread_Graph.spread_width - 25)
                        .attr("y2", y_coordinate + svg_middle_y + offset)
                        .attr("stroke-width",3)
                        .attr("class","my_line");
                    Spread_Graph.addOthersLineAnimation([your_spread_line_top, your_spread_line_bottom], 500, 25); 
                    setTimeout(function(d){
                        Spread_Graph.drawSpreadBar(my_spread,svg_middle_y,y_coordinate, offset, key);
                    }, 500);
                }else{

                    //Where the grey middle line is
                    svg_middle_y = Spread_Graph.spread_height/2;
                    my_spread = parseInt(newLines[key]["A"] - newLines[key]["B"]);
                    money_ratio =  oTreeConstants.max_spread/my_spread;
                    y_coordinate = svg_middle_y/money_ratio;
                    // console.log(y_coordinate);
                   var your_spread_line_top = Spread_Graph.spread_svg.append("svg:line")
                        .attr("x1",Spread_Graph.spread_width)
                        .attr("y1", svg_middle_y - y_coordinate)
                        .attr("x2", Spread_Graph.spread_width - 15)
                        .attr("y2", svg_middle_y - y_coordinate)
                        .attr("stroke-width",1)
                        .attr("class","others_line");
                
                    var your_spread_line_bottom = Spread_Graph.spread_svg.append("svg:line")
                        .attr("x1", Spread_Graph.spread_width)
                        .attr("y1", y_coordinate + svg_middle_y)
                        .attr("x2", Spread_Graph.spread_width - 15)
                        .attr("y2", y_coordinate + svg_middle_y)
                        .attr("stroke-width",1)
                        .attr("class","others_line");
                    // for removing when a transation occurs
                    Spread_Graph.addOthersLineAnimation([your_spread_line_top, your_spread_line_bottom], 500, 15);
                }
                Spread_Graph.spread_lines[key] = newLines[key];
            }
            if(inv == true){
               var spread_line_fundamental_price = Spread_Graph.spread_svg.append("svg:line")
                    .attr("x1", 0 + 50)
                    .attr("y1", Spread_Graph.spread_height/2)
                    .attr("x2", Spread_Graph.spread_width - 50)
                    .attr("y2", Spread_Graph.spread_height/2)
                    .style("stroke", "yellow")
                    .style("stroke-width", 10)
                    .attr("class", "inv-line");
            }
            
            var spread_line_fundamental_price = Spread_Graph.spread_svg.append("svg:line")
                .attr("x1", 0 + 60)
                .attr("y1", Spread_Graph.spread_height/2)
                .attr("x2", Spread_Graph.spread_width - 60)
                .attr("y2", Spread_Graph.spread_height/2)
                .style("stroke", "grey")
                .style("stroke-width", 3);
            if(inv == true){
                setTimeout(function(){
                    d3.selectAll(".inv-line").remove();
                },400);
            }
  }

 addOthersLineAnimation(lines, speed=500, width){
      //SETTING THE SPREAD TO THE LINE
      for(var i = 0; i < lines.length; i++){
          var add_animation = lines[i]
            .transition()
            .duration(speed)
            .attr("x1", (Spread_Graph.spread_width / 2) + width)
            .attr("x2", (Spread_Graph.spread_width / 2) - width);
      }      
  }

  drawSpreadBar(my_spread,svg_middle_y,y_coordinate, offset, id){
        //take into account
        console.log(y_coordinate);
        var bar_color = "";
        //if not other maker within the spread
        if(id == oTreeConstants.smallest_spread["key"]){
            bar_color = "green_bar";
        }else{
            bar_color = "blue_bar";
        }
        var your_bar_rect = Spread_Graph.spread_svg.append("svg:rect")
                   .attr("x", (Spread_Graph.spread_width / 2) - 25)
                   .attr("y", Spread_Graph.spread_height/2 - y_coordinate)
                   .attr("width", 50)
                   .attr("height", 2*y_coordinate)
                   .attr("class",bar_color);
    }
  
    drawTransactionBar(my_spread,svg_middle_y,y_coordinate, side, color){
      //take into account
      var bar_color = color;
      //if not other maker within the spread
      if(side == "B"){
          var your_bar_rect = Spread_Graph.spread_svg.append("svg:rect")
              .attr("x", (Spread_Graph.spread_width / 2) - 5)
              .attr("y", svg_middle_y)
              .attr("width", 10)
              .attr("height",y_coordinate)
              .attr("class",bar_color);
      } else if(side == "S"){
         var your_bar_rect = Spread_Graph.spread_svg.append("svg:rect")
                  .attr("x", (Spread_Graph.spread_width / 2) - 5)
                  .attr("y", svg_middle_y - y_coordinate)
                  .attr("width", 10)
                  .attr("height", y_coordinate)
                  .attr("class",bar_color);
      }
    }
    updateSmallest(key){
      console.log(key +  " this is the key");
            delete oTreeConstants.smallest_spread[key];
            smallest_spread[-1] = oTreeConstants.max_spread;
            for(var key in spread_lines){
                if((spread_lines[key]["A"] - Spread_Graph.spread_lines[key]["B"]) < smallest_spread["spread"]){
                    smallest_spread["key"] = key;
                    smallest_spread["spread"] = Spread_Graph.spread_lines[key]["A"] - Spread_Graph.spread_lines[key]["B"]
                }
            }
        }

    clear(){
      Spread_Graph.spread_svg.selectAll(".my_line").remove();
      Spread_Graph.spread_svg.selectAll(".others_line").remove();
      Spread_Graph.spread_svg.selectAll("rect").remove();
    }
    drawTransactionBar(lines, speed=500, width){
        //SETTING THE SPREAD TO THE LINE

        for(i = 0; i < lines.length; i++){
            var add_animation = lines[i]
              .transition()
              .duration(speed)
              .attr("x1", (Spread_Graph.spread_width / 2) + width)
              .attr("x2", (Spread_Graph.spread_width / 2) - width);
        }      
    }

  }

window.customElements.define('spread-graph', SpreadGraph);
