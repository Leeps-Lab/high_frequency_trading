import {html,PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';

/**
 * @customElement
 * @polymer
 */
class InputSection extends PolymerElement {

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

    interactiveComponent.inputSectionDOM = interactiveComponent.interactiveComponentShadowDOM.querySelector("input-section");
    interactiveComponent.inputSectionDOM.attachShadow({mode: 'open'});

    inputSection.inputSectionShadowDOM =  interactiveComponent.inputSectionDOM.shadowRoot;
    inputSection.inputSectionShadowDOMD3 = d3.select(inputSection.shadow_dom);
    //Second we add the HTML neccessary to be manipulated in the constructor and the subsequent functions
    inputSection.inputSectionShadowDOM.innerHTML = `
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
    
        .button-container{
            background-color: rgb(230, 230, 230);
            padding-bottom: 5px;
            flex: 1 1 auto;
            display: flex;
            justify-content: center;
            flex-direction: column;
        }
        
        .slider{
            -webkit-appearance: slider-vertical;
        }
        .submit-button{
            margin-top:85px;
        }
        .button-container-speed {
            background-color: rgb(230, 230, 230);
            flex: 1 1 auto;
        }
        .slider-sens{
            margin-top:10px;
        }

        .switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
          }
          
          .switch .speed-input { 
            opacity: 0;
            width: 0;
            height: 0;
          }
          
          .slider-speed {
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
          
          .slider-speed:before {
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
          
          .speed-input:checked + .slider-speed {
            background-color: #2196F3;
          }
          
          .speed-input:focus + .slider-speed {
            box-shadow: 0 0 1px #2196F3;
          }
          
          .speed-input:checked + .slider-speed:before {
            -webkit-transform: translateX(26px);
            -ms-transform: translateX(26px);
            transform: translateX(26px);
          }
          
          /* Rounded sliders */
          .slider-speed.round {
            border-radius: 34px;
          }
          
          .slider-speed.round:before {
            border-radius: 50%;
          }
    </style>
    
    <div class="container-fluid">

    <div class="row">
        <div class="text-center col-lg-3">
            <button  value="out" class="text-center btn btn-primary manual-button" type="button"  width="80px">Manual</button>
            <div class="slider-sens" style="margin-top:50px;">
                <button   class="text-center btn btn-primary submit-button" type="button">Submit Values</button>
            </div>
        </div>
        <div class="text-center col-lg-3" >
            <button class="text-center btn btn-primary algorithm-button maker-button" type="button"  width="80px">Maker</button>
            <div class="slider-sens" style="margin-top:50px;">
                <p>Sensitivity value <b><span id="sens_1_output"></span></b></p>
                <input type="range" min="-1" max="1" value="0" class="slider" id="sens_1" step="0.1">
            </div>
        </div>
        <div class="text-center col-lg-3">
            <button class="text-center btn btn-primary taker-button taker-button" type="button" width="80px">Taker</button>
            <div class="slider-sens" style="margin-top:50px;">
                <p>Sensitivity value <b><span id="sens_2_output"></span></b></p>
                <input type="range" min="-1" max="1" value="0" class="slider" id="sens_2" step="0.1">
            </div>
        </div>
        <div class="text-center col-lg-3">
            <button class="text-center btn btn-primary out-button" type="button" width="80px">Out</button>
            <div class="text-center center-block" style="margin-top:100px;">
                <p>Speed</p>
                <label class="switch">
                    <input type="checkbox" class="speed-input">
                    <span class="slider-speed round"></span>
                </label>
            </div>
        </div>
    </div>
    <!---
    <div class="row">
          <div>
            <button  class="center-block btn btn-primary test-cancel-button" type="button">Test Cancel</button>
          </div>
          <div>
            <button  class="center-block btn btn-primary test-replace-button" type="button">Test Replace</button>
          </div>
          <div>
            <button  class="center-block btn btn-primary test-confirmation-button" type="button">Test Confirmation</button>
          </div>
          <div>
            <button  class="center-block btn btn-primary test-BBO-button" type="button">Test BBO</button>
          </div>
    </div>
    --->
    </div>
    
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
        
    `;

    //Start as speed false
    this.speed = false;
   
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
    inputSection.manualClick = this.manualClick;
    inputSection.makerClick = this.makerButton;
    inputSection.takerClick = this.takerButton;
    inputSection.submitClick = this.submitButton;
    inputSection.outClick = this.outButton;
    inputSection.uncheckOtherButtons = this.uncheckOtherButtons;

    inputSection.testClick = this.testButton;

    this.activateSliders();
    this.activateButtons();

  }

  activateSliders() {
        
        var sens1 = inputSection.inputSectionShadowDOM.querySelector("#sens_1");
        var sens1Output = inputSection.inputSectionShadowDOM.querySelector("#sens_1_output");
        var sens2 = inputSection.inputSectionShadowDOM.querySelector("#sens_2");
        var sens2Output = inputSection.inputSectionShadowDOM.querySelector("#sens_2_output");
        sens1Output.innerHTML = sens1.value;
        sens2Output.innerHTML = sens2.value;
    
        sens1.oninput = function() {

            sens1Output.innerHTML = this.value;
        }
        sens2.oninput = function() {
        
            sens2Output.innerHTML = this.value;
        }
      
  }
  activateButtons(){
    var manualButton = inputSection.inputSectionShadowDOM.querySelector(".manual-button");
    var makerButton = inputSection.inputSectionShadowDOM.querySelector(".maker-button");
    var takerButton = inputSection.inputSectionShadowDOM.querySelector(".taker-button");
    var outButton = inputSection.inputSectionShadowDOM.querySelector(".out-button");
    var submitButton = inputSection.inputSectionShadowDOM.querySelector(".submit-button");
    
    // var testCancelButton = inputSection.inputSectionShadowDOM.querySelector(".test-cancel-button");
    // var testReplaceButton = inputSection.inputSectionShadowDOM.querySelector(".test-replace-button");
    // var testConfirmationButton = inputSection.inputSectionShadowDOM.querySelector(".test-confirmation-button");
    // var testBBOButton = inputSection.inputSectionShadowDOM.querySelector(".test-BBO-button");

    manualButton.onclick = inputSection.manualClick;
    makerButton.onclick = inputSection.makerClick;
    takerButton.onclick = inputSection.takerClick;
    outButton.onclick = inputSection.outClick;
    submitButton.onclick = inputSection.submitClick;

    // var testCancel = function () { inputSection.testClick("cancel")};
    // var testReplace = function () { inputSection.testClick("replace")};
    // var testConfirmation = function () { inputSection.testClick("confirmation")};
    // var testBBO = function () { inputSection.testClick("BBO")};

    // testCancelButton.onclick = testCancel;
    // testReplaceButton.onclick = testReplace;
    // testConfirmationButton.onclick = testConfirmation;
    // testBBOButton.onclick = testBBO;

  } 


    manualClick(){
        inputSection.uncheckOtherButtons(this);
        //update player object 
        this.classList.toggle("btn-primary");
        this.classList.toggle("btn-success");
        playersInMarket[otree.playerID]["strategy"] = "maker_basic";
        var manualChangeMessage = {
            type: "role_change",
            state: playersInMarket[otree.playerID]["strategy"]
        };
        if(socketActions.socket.readyState === socketActions.socket.OPEN){
            console.log(JSON.stringify(manualChangeMessage));
            socketActions.socket.send(JSON.stringify(manualChangeMessage));
        }
        //start the drawArrows on the spread graph only if there are none at the price you either left or at some designated start price or best price?
        spreadGraph.removeArrows();
        spreadGraph.drawArrows();
        

        //disable all sliders and and submit button 
        var submitButton = inputSection.inputSectionShadowDOM.querySelector(".submit-button");
        var sens1 = inputSection.inputSectionShadowDOM.querySelector("#sens_1");
        var sens2 = inputSection.inputSectionShadowDOM.querySelector("#sens_2");
        submitButton.disabled = true;
        sens1.disabled = true;
        sens2.disabled = true;

    }

    makerButton(){
        inputSection.uncheckOtherButtons(this);
        //update player object 
        playersInMarket[otree.playerID]["strategy"] = "maker_2";
        var makerBasicChangeMessage = {
            type: "role_change",
            id: otree.playerID,
            id_in_group: otree.playerIDInGroup,
            state: playersInMarket[otree.playerID]["strategy"]
        };
        if(socketActions.socket.readyState === socketActions.socket.OPEN){
            console.log(JSON.stringify(makerBasicChangeMessage));
            socketActions.socket.send(JSON.stringify(makerBasicChangeMessage));
        }
        //s
        spreadGraph.removeArrows();
        spreadGraph.drawArrows();
        
        var submitButton = inputSection.inputSectionShadowDOM.querySelector(".submit-button");
        var sens1 = inputSection.inputSectionShadowDOM.querySelector("#sens_1");
        var sens2 = inputSection.inputSectionShadowDOM.querySelector("#sens_2");
        submitButton.disabled = false;
        sens1.disabled = false;
        sens2.disabled = false;

    }

    takerButton(){
        inputSection.uncheckOtherButtons(this);
        playersInMarket[otree.playerID]["strategy"] = "taker";
        var algorithm2ChangeMessage = {
            type: "role_change",
            id: otree.playerID,
            id_in_group: otree.playerIDInGroup,
            state: playersInMarket[otree.playerID]["strategy"]
        };
        if(socketActions.socket.readyState === socketActions.socket.OPEN){
            console.log(JSON.stringify(algorithm2ChangeMessage));
            socketActions.socket.send(JSON.stringify(algorithm2ChangeMessage));
        }
        spreadGraph.removeArrows();
        var submitButton = inputSection.inputSectionShadowDOM.querySelector(".submit-button");
        var sens1 = inputSection.inputSectionShadowDOM.querySelector("#sens_1");
        var sens2 = inputSection.inputSectionShadowDOM.querySelector("#sens_2");
        submitButton.disabled = true;
        sens1.disabled = true;
        sens2.disabled = true;

    }

    submitButton(){
        var sens1 = inputSection.inputSectionShadowDOM.querySelector("#sens_1");
        var sens2 = inputSection.inputSectionShadowDOM.querySelector("#sens_2");
        var sens1Value = sens1.value;
        var sens2Value = sens2.value;
        var algorithm2ChangeMessage = {
            type: "submit_sensitivities",
            id: otree.playerID,
            id_in_group: otree.playerIDInGroup,
            state: playersInMarket[otree.playerID]["strategy"]
        };
        if(socketActions.socket.readyState === socketActions.socket.OPEN){
            console.log(JSON.stringify(algorithm2ChangeMessage));
            socketActions.socket.send(JSON.stringify(algorithm2ChangeMessage));
        }

        

    }

    outButton(){
        inputSection.uncheckOtherButtons(this);
        spreadGraph.removeArrows();
        playersInMarket[otree.playerID]["strategy"] = "out";
        var outChangeMessage = {
            type: "role_change",
            id: otree.playerID,
            id_in_group: otree.playerIDInGroup,
            state: playersInMarket[otree.playerID]["strategy"]
        };
        if(socketActions.socket.readyState === socketActions.socket.OPEN){
            console.log(JSON.stringify(outChangeMessage));
            socketActions.socket.send(JSON.stringify(outChangeMessage));
        }
        var submitButton = inputSection.inputSectionShadowDOM.querySelector(".submit-button");
        var sens1 = inputSection.inputSectionShadowDOM.querySelector("#sens_1");
        var sens2 = inputSection.inputSectionShadowDOM.querySelector("#sens_2");
        submitButton.disabled = true;
        sens1.disabled = true;
        sens2.disabled = true;

    }

    uncheckOtherButtons(button){
        console.log(button.className);
    }

    testButton(testing){

        var msg = {};

        if(testing === "cancel"){
            msg["canceled"] = {};
            msg["canceled"]["type"] = otree.playerID ;
            msg["canceled"]["order_token"] = "TESTTOKEN1";
            msg["canceled"]["price"] = 980000;
        } else if(testing === "replace"){
            msg["replaced"] = {};
            msg["replaced"]["type"] = otree.playerID;
            msg["replaced"]["order_token"] = "TESTTOKEN1";
            msg["replaced"]["replaced_token"] = "TESTTOKEN0";
            msg["replaced"]["price"] = 980000;
        } else if(testing === "confirmation"){
            msg["confirmed"] = {};
            msg["confirmed"]["type"] = otree.playerID ;
            msg["confirmed"]["order_token"] = "TESTTOKEN0";
            msg["confirmed"]["price"] = 930000;
        } else if(testing === "BBO"){
            msg["bbo"] = {};
            msg["bbo"]["type"] = otree.marketID;
            msg["bbo"]["best_bid"] = 950000;
            msg["bbo"]["best_offer"] = 970000;
            
        }
        
        // msg["trader"]["price"] = 920000;
        JSON.stringify(msg);
        console.log("Message being tested below");
        console.log(msg);
        alert("Tested message being sent");
        otree.testMessageHandler(msg);

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