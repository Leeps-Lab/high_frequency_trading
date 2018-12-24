import {html,PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';

/**
 * @customElement
 * @polymer
 */
class InputSection extends PolymerElement {
  static get template() {
    return html`
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
<style>
    .button-on{
        background-color:steelblue;
        border-color: solid black 5px;
        color:white;
        border-color: black;
        border-width: 2px;
    }

    .button-on-sniper{
        background-color:orangered;
        border-color: solid black 5px;
        color:white;
        border-color: black;
        border-width: 2px;
    }

    .button-pressed{
        background-color:#444444;
        color:white;
    }
    .button-off{
        background-color:#666666;
        color:white;
    }
    #speed_checkbox{
        margin-left:30px;
        margin-top:20px;
    }

    .button-container{
        background-color: rgb(230, 230, 230);
        padding-bottom: 5px;
        flex: 1 1 auto;
        display: flex;
        justify-content: center;
        flex-direction: column;
    }



    .button-container-speed {
        background-color: rgb(230, 230, 230);
        flex: 1 1 auto;
    }

    /* The switch - the box around the slider */
    .switch {
        position: relative;
        display: inline-block;
        width: 60px;
        height: 34px;
    }

    /* Hide default HTML checkbox */
    .switch #speed_checkbox {display:none;}

    /* The slider */
    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        -webkit-transition: .4s;
        transition: .4s;
    }

    .slider:before {
        position: absolute;
        content: "";
        height: 26px;
        width: 26px;
        left: 4px;
        bottom: 4px;
        background-color: white;
        -webkit-transition: .4s;
        transition: .4s;
    }

    #speed_checkbox:checked + .slider {
        background-color: #1fd15a;
    }

    #speed_checkbox:focus + .slider {
        box-shadow: 0 0 1px #1fd15a;
    }

    #speed_checkbox:checked + .slider:before {
        -webkit-transform: translateX(26px);
        -ms-transform: translateX(26px);
        transform: translateX(26px);
    }

    /* Rounded sliders */
    .slider.round {
        border-radius: 34px;
    }

    .slider.round:before {
        border-radius: 50%;
    }
</style>
<!--
<div class="row">
    <div class=" col-xs-3">
        <button id="out" value="out" class="button-on" on-click="outClick" type="button" style="width:80px">Out</button>
    </div>
    <div class=" col-xs-3">
        <button id="sniper" value="sniper" class="button-off" on-click="sniperClick" type="button" style="width:80px">Sniper</button> 
    </div>
    <div class=" col-xs-3">
        <button id="maker" value="maker" class="button-off" on-click="makerClick" type="button" style="width:80px">Maker</button>
    </div>
    <div class=" col-xs-3">
        <p style="text-align: center; font-size:16px; margin-left: 50%; margin-top:40px;">Speed</p>
        <label class="switch" style="margin-left: 50%; margin-top: -10px;" >
                <br>
                <input id="speed_checkbox" type="checkbox" on-click="updateSpeed">
                <span class="slider round"></span>
        </label>
    </div>
</div>
<br>
-->

<div class="container-fluid">
<div class="row">
    <div class="text-center col-lg-3" style="border:solid black 1px;">
        <button  value="out" class="text-center btn btn-primary" on-click="outClick" type="button">Manual</button>
        <br>
        <br>
        
        <button  value="out" class="text-center btn btn-primary" on-click="outClick" type="button">Submit Sensitivities</button>
    </div>
    <div class="text-center col-lg-3" style="border:solid black 1px;">
        <button  value="out" class="text-center btn btn-primary" on-click="outClick" type="button">Algorithm A</button>
        <br>
        <br>
        <p>Sensitivity value <b><span id="sens_1_output"></span></b></p>

        <input type="range" min="-1" max="1" value="0" class="slider" id="sens_1" step="0.1">
    </div>
    <div class="text-center col-lg-3" style="border:solid black 1px;">
        <button value="out" class="text-center btn btn-primary" on-click="outClick" type="button">Algorithm B</button>
        <br>
        <br>
        <p>Sensitivity value <b><span id="sens_2_output"></span></b></p>
        <input type="range" min="-1" max="1" value="0" class="slider" id="sens_2" step="0.1">
    </div>
    <div class="text-center col-lg-3">
        <p>Speed</p>
        <label class="switch" >
                <br>
                <input id="speed_checkbox" type="checkbox" on-click="updateSpeed">
                <span class="slider round"></span>
        </label>
    </div>
</div>
</div>

<script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
    `;
  }

  static get properties() {
    return {
      player_id: {
        type: String,
        value:"this"
        }
      };
  }

  constructor() {
    super();
    this.socket = socketActions.socket;
   
    //Start as speed false
    this.speed = false;
    interactiveComponent.inputSectionDOM = interactiveComponent.interactiveComponentShadowDOM.querySelector("input-section");
    interactiveComponent.inputSectionDOM.attachShadow({mode: 'open'});
    inputSection.inputSectionShadowDOM =  interactiveComponent.inputSectionDOM.shadowRoot;
    inputSection.inputSectionShadowDOM = d3.select(inputSection.shadow_dom);
    
    alert("Fuck this");
    if(otree.FBA){
            //INPUT SECTION
        inputSection.shadow_dom_D3.append("svg").attr("id","timer_FBA");
        inputSection.timerSVGDOM = inputSection.shadow_dom.querySelector("#timer_FBA");
        inputSection.timerSVG = d3.select(inputSection.timerSVGDOM);
        inputSection.drawTimer = this.drawTimer;
        inputSection.startTimer = this.startTimer;
        inputSection.drawTimer();
    }

    inputSection.Button_Pressed = this.Button_Pressed;
    inputSection.startBatchTimer = this.startBatchTimer;
    inputSection.updateSpeed = this.updateSpeed;
    
    this.activateSliders();

  }

  activateSliders() {
        
        var sens1 = document.getElementById("sens_1");
        console.log(document);
        var sens1Output = document.getElementById("sens_1_output");
        var sens2 = document.getElementById("sens_2");
        console.log(sens2);
        var sens2Output = document.getElementById("sens_2_output");
        // sens1Output.innerHTML = sens1.value;
        // sens2Output.innerHTML = sens2.value;
    
        // sens1.oninput = function() {
        //     console.log(this.value);
        //     sens1Output.innerHTML = this.value;
        // }
        // sens2.oninput = function() {
        //     console.log(this.value);
        //     sens2Output.innerHTML = this.value;
        // }
      
  } 

  makerClick(input_object){

    if ((input_object.path[0].className  == "button-off") && (input_object.path[0].className != "button-pressed") && (input_object.path[1].querySelector("#sniper").className != "button-pressed")){
    //     //IF BUTTON IS NOT PRESSED OR ON THEN TURN IT ON AFTER DELAD (Button_Pressed())

        /* 
        * Some Wizadry to differentiate between the inputs inside of the input-selection DOM element
        * input_object.path[0] is the button that is being clicked
        * input_object.path[1] is the actual input-selection element (Shadow DOM that we create using Polymer 3.0), once we access this -
        * the querySelector can then access each input and we can */
        input_object.path[0].className = "button-pressed";

        var timeNow = profitGraph.getTime();
            profitGraph.profitSegments.push(
                {
                    startTime:timeNow,
                    endTime:timeNow, 
                    startProfit:profitGraph.profit, 
                    endProfit:profitGraph.profit,
                    state:"MAKER"
                }
            );

        var msg = {
            type: 'role_change',
            id: otree.playerID ,
            id_in_group: otree.playerIDInGroup,
            state: "MAKER"
        };

        var speed_msg = {
            type: 'speed_change',
            id: otree.playerID ,
            id_in_group: otree.playerIDInGroup,
            speed: false 
        };

        if (this.socket.readyState === this.socket.OPEN) {
          this.socket.send(JSON.stringify(msg));
          if(this.speed){
            this.socket.send(JSON.stringify(speed_msg));
            this.speed = !this.speed;
            input_object.path[1].querySelector("#speed_checkbox").checked = false;
            document.querySelector('info-table').setAttribute("speed_cost","0");
          }
        }


        var money_ratio =  otree.maxSpread/(spreadGraph.last_spread * 10000);
        var svg_middle_y = spreadGraph.spread_height/2;
        var y_coordinate = svg_middle_y/money_ratio;
        
        spreadGraph.drawLineAttempt(y_coordinate);

       this.Button_Pressed(input_object);
       document.querySelector('info-table').setAttribute("player_role","MAKER"); 
       document.querySelector('info-table').setAttribute("spread_value",spreadGraph.last_spread.toFixed(2));
    }
     input_object.path[1].querySelector("#out").className = "button-off";
     input_object.path[1].querySelector("#sniper").className = "button-off";
  }

  sniperClick(input_object){
    if ((input_object.path[0].className  == "button-off") && (input_object.path[0].className != "button-pressed") && (input_object.path[1].querySelector("#maker").className != "button-pressed")){
    //     //IF BUTTON IS NOT PRESSED OR ON THEN TURN IT ON AFTER DELAD (Button_Pressed())

        /* 
        * Some Wizadry to differentiate between the inputs inside of the input-selection DOM element
        * input_object.path[0] is the button that is being clicked
        * input_object.path[1] is the actual input-selection element (Shadow DOM that we create using Polymer 3.0), once we access this -
        * the querySelector can then access each input and we can 
        */

        input_object.path[0].className = "button-pressed";

        var timeNow = profitGraph.getTime() - otree.timeOffset;
            profitGraph.profitSegments.push(
                {
                    startTime:timeNow,
                    endTime:timeNow, 
                    startProfit:profitGraph.profit, 
                    endProfit:profitGraph.profit,
                    state:"SNIPER"
                }
            );

        var msg = {
            type: 'role_change',
            id: otree.playerID ,
            id_in_group: otree.playerIDInGroup,
            state: "SNIPER"
        };
        var speed_msg = {
              type: 'speed_change',
              id: otree.playerID ,
              id_in_group: otree.playerIDInGroup,
              speed: false 
          };
        if (this.socket.readyState === this.socket.OPEN) {
          this.socket.send(JSON.stringify(msg));
          if(this.speed){
            this.socket.send(JSON.stringify(speed_msg));
            this.speed = !this.speed;
            input_object.path[1].querySelector("#speed_checkbox").checked = false;
            document.querySelector('info-table').setAttribute("speed_cost","0");
          }
        }

       this.Button_Pressed(input_object);
       document.querySelector('info-table').setAttribute("player_role","SNIPER"); 
    }
    spreadGraph.spread_svg.selectAll("rect").remove();
    spreadGraph.spread_svg.selectAll(".my_line").remove();
    delete spreadGraph.spread_lines[otree.playerID]
    delete spreadGraph.spreadLinesFBAConcurrent[otree.playerID]
     document.querySelector('info-table').spread_value = 0;
     input_object.path[1].querySelector("#maker").className = "button-off";
     input_object.path[1].querySelector("#out").className = "button-off";
     document.querySelector('info-table').setAttribute("curr_bid","N/A");
     document.querySelector('info-table').setAttribute("curr_ask","N/A");
  }

  outClick(input_object){
    if ((input_object.path[0].className  == "button-off") && (input_object.path[0].className != "button-pressed") && (input_object.path[1].querySelector("#maker").className != "button-pressed")&& (input_object.path[1].querySelector("#sniper").className != "button-pressed")){
        //IF BUTTON IS NOT PRESSED OR ON THEN TURN IT ON AFTER DELAD (Button_Pressed())
        /* 
        * Some Wizadry to differentiate between the inputs inside of the input-selection DOM element
        * input_object.path[0] is the button that is being clicked
        * input_object.path[1] is the actual input-selection element (Shadow DOM that we create using Polymer 3.0), once we access this -
        * the querySelector can then access each input and we can */
        input_object.path[0].className = "button-on";
        var timeNow = profitGraph.getTime();

        profitGraph.profitSegments.push(
                {
                    startTime:timeNow,
                    endTime:timeNow, 
                    startProfit:profitGraph.profit, 
                    endProfit:profitGraph.profit,
                    state:"OUT"
                }
            );
        var msg = {
            type: 'role_change',
            id: otree.playerID ,
            id_in_group: otree.playerIDInGroup,
            state: "Out"
        };
        var speed_msg = {
              type: 'speed_change',
              id: otree.playerID ,
              id_in_group: otree.playerIDInGroup,
              speed: this.speed 
          };

          if (this.socket.readyState === this.socket.OPEN) {
              this.socket.send(JSON.stringify(msg));
              if(this.speed){
                this.socket.send(JSON.stringify(speed_msg));
                this.speed = !this.speed;
                input_object.path[1].querySelector("#speed_checkbox").checked = false;
                document.querySelector('info-table').setAttribute("speed_cost","0");
              }
          } 
       document.querySelector('info-table').setAttribute("player_role","OUT"); 
    }

     input_object.path[1].querySelector("#sniper").className = "button-off";
     input_object.path[1].querySelector("#maker").className = "button-off";
     //Turn off Speed if it is on the front end
     document.querySelector('info-table').setAttribute("speed_cost",0);
     console.log("Out now");
     document.querySelector('info-table').setAttribute("spread_value",0);
     document.querySelector('info-table').setAttribute("curr_bid","N/A");
     document.querySelector('info-table').setAttribute("curr_ask","N/A");

     spreadGraph.spread_svg.selectAll("rect").remove();
     spreadGraph.spread_svg.selectAll(".my_line").remove();
    delete spreadGraph.spread_lines[otree.playerID];
    delete spreadGraph.spreadLinesFBAConcurrent[otree.playerID];
    
  }

  drawTimer(){
    inputSection.inputWidth = document.querySelector("input-section").clientWidth*1.5;
    inputSection.inputHeight = document.querySelector("input-section").clientHeight;
    inputSection.timerSVGDOM.style.width = inputSection.inputWidth;
    inputSection.timerSVGDOM.style.height = 7;
    inputSection.timerSVGDOM.style.marginBottom = "20px";
    inputSection.timerSVGDOM.style.marginLeft = "30px";
    inputSection.timerSVGDOM.style.backgroundColor = "lightgrey";
    inputSection.inputX = inputSection.shadow_dom.querySelector("#timer_FBA").getBoundingClientRect().left;
    inputSection.inputY = inputSection.shadow_dom.querySelector("#timer_FBA").getBoundingClientRect().top;
  }

  startTimer(){
    inputSection.timerSVG.selectAll("#timer-line").remove();
    var timerLine = inputSection.timerSVG.append("svg:line")
                       .attr("x1", 0)
                       .attr("y1", 0)
                       .attr("x2", 0)
                       .attr("y2", 0)
                       .attr("id","timer-line")
                       .style("stroke", "purple")
                       .style("stroke-width", 10);

    timerLine.transition()
            .duration(otree.batchLength*1100)
            .attr("x2", inputSection.inputWidth);
  }

   Button_Pressed(input_object){
        //Wait .5 seconds for button pressed to even for fast players
        // to eliminate spam clicking
        var button_timer = setTimeout(this.Button_Change.bind(null,input_object),500);
    }
   Button_Change(input_object){
        //turning button on after the delay
        var id = input_object.path[0].id;
        if(id == "sniper"){
          input_object.path[0].className = "button-on-sniper";
        } else {
          input_object.path[0].className = "button-on";
        }
    }

    updateSpeed(input_object){
      console.log("Called at least");
      console.log(document.querySelector('info-table').getAttribute("player_role"));
      if(document.querySelector('info-table').getAttribute("player_role") != "OUT"){
        console.log("Inside the if");
          //If you arent out you can turn your speed on
          this.speed = !this.speed;
          if(this.speed){
              document.querySelector('info-table').setAttribute("speed_cost",(otree.speedCost * (1e-4) * (1e9)).toFixed(3));
          }else {
              document.querySelector('info-table').setAttribute("speed_cost",0);
          }
        var timeNow = profitGraph.getTime() - profitGraph.timeOffset;
        profitGraph.profitSegments.push(
            {
                startTime:timeNow,
                endTime:timeNow, 
                startProfit:profitGraph.profit, 
                endProfit:profitGraph.profit,
                state:document.querySelector('info-table').player_role
            }
        );

          var msg = {
              type: 'speed_change',
              id: otree.playerID ,
              id_in_group: otree.playerIDInGroup,
              speed: this.speed
          };

          if (this.socket.readyState === this.socket.OPEN) {
              this.socket.send(JSON.stringify(msg));
          } 
      } else {
         input_object.path[0].checked = false;
      }
    }


}
window.customElements.define('input-section', InputSection);