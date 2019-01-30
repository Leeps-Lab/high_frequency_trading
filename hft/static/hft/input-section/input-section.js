import {html,PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';

/**
 * @customElement
 * @polymer
 */
class InputSection extends PolymerElement {
  constructor() {
    super();

    interactiveComponent.inputSectionDOM = interactiveComponent.interactiveComponentShadowDOM.querySelector("input-section");
    interactiveComponent.inputSectionDOM.attachShadow({mode: 'open'});

    inputSection.inputSectionShadowDOM =  interactiveComponent.inputSectionDOM.shadowRoot;
    inputSection.inputSectionShadowDOMD3 = d3.select(inputSection.shadow_dom);
    //Second we add the HTML neccessary to be manipulated in the constructor and the subsequent functions
    inputSection.inputSectionShadowDOM.innerHTML = `
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
    <link rel="stylesheet" href="/static/hft/input-section/range.css">
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
            background-color: rgb(200, 200, 200);
            padding-bottom: 5px;
            flex: 1 1 auto;
            display: flex;
            justify-content: center;
            flex-direction: column;
        }
        
        .slider{
            
        }
       
        .button-container-speed {
            background-color: rgb(230, 230, 230);
            flex: 1 1 auto;
        }
        .slider-sens{
            margin-top: 20px;
        }

        .slider-sens > input {
            width: 100%;
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
    

   <div class="container-fluid" style="height: 100%;">
    <div class="row" style="height: 100%;">
        <div class="text-center col-lg-2">
            <div class="text-center center-block" style="margin-top:10px;">
                <p>Speed</p>
                <label class="switch">
                <input type="checkbox" class="speed-input">
                <span class="slider-speed round"></span>
                </label>
            </div>
        </div>
    
        <div class="text-center col-lg-2">
            <div style="margin-top:15px;">
                <button  value="out" class="text-center btn btn-block btn-primary manual-button" type="button">Manual</button>
                <button class="text-center btn btn-block btn-primary btn-success out-button" type="button">Out</button>
            </div>
        </div>
        
        <div class="text-center col-lg-8" style="background-color:rgb(200,200,200);">
            <div class="row">
                <div class="col-lg-4">
                    <div style="margin-top: 15px">
                        <button class="text-center btn btn-block btn-primary algorithm-button maker-button" type="button">Maker</button>
                        <button class="text-center btn btn-block btn-primary taker-button taker-button" type="button">Taker</button>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="slider-sens" >
                        <p>Val 1 <b><span id="sens_1_output"></span></b></p>
                        <input type="range" min="-1" max="1" value="0" class="slider" id="sens_1" step="0.1">
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="slider-sens" >
                        <p>Val 2: <b><span id="sens_2_output"></span></b></p>
                        <input type="range" min="-1" max="1" value="0" class="slider" id="sens_2" step="0.1">
                    </div>
                </div>
            </div>
        </div>


    </div>
    </div>
    `;

    //Start as speed false
    this.speed = false;


    inputSection.manualClick = this.manualClick;
    inputSection.makerClick = this.makerButton;
    inputSection.takerClick = this.takerButton;
    inputSection.submitButton= this.submitButton;
    inputSection.outClick = this.outButton;
    inputSection.sendSpeed = this.sendSpeed;
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
        sens1.disabled = true;
        sens2.disabled = true;
        playersInMarket[otree.playerID]["strategy"] = "out";  
        sens1.onchange = function() {inputSection.submitButton()};
        sens2.onchange = function() {inputSection.submitButton()};
    
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
    var speed = inputSection.inputSectionShadowDOM.querySelector(".speed-input");
    
    // var testCancelButton = inputSection.inputSectionShadowDOM.querySelector(".test-cancel-button");
    // var testReplaceButton = inputSection.inputSectionShadowDOM.querySelector(".test-replace-button");
    // var testConfirmationButton = inputSection.inputSectionShadowDOM.querySelector(".test-confirmation-button");
    // var testBBOButton = inputSection.inputSectionShadowDOM.querySelector(".test-BBO-button");

    manualButton.onclick = inputSection.manualClick;
    makerButton.onclick = inputSection.makerClick;
    takerButton.onclick = inputSection.takerClick;
    outButton.onclick = inputSection.outClick;

    speed.onclick = inputSection.sendSpeed;

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
        if(inputSection.inputSectionShadowDOM.querySelector(".speed-input").checked == true){
            inputSection.inputSectionShadowDOM.querySelector(".speed-input").checked = false;
            inputSection.sendSpeed();
        }
        inputSection.uncheckOtherButtons(this);   
        inputSection.inputSectionShadowDOM.querySelector(".manual-button").classList.toggle("btn-success");
        inputSection.inputSectionShadowDOM.querySelector(".speed-input").disabled = false;
        playersInMarket[otree.playerID]["strategy"] = "maker_basic";   
        // interactiveComponent.interactiveComponentShadowDOM.querySelector("information-table").updateState("bbo");;
       
        // infoTable.updateRole("Manual");  
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
        // var submitButton = inputSection.inputSectionShadowDOM.querySelector(".submit-button");
        var sens1 = inputSection.inputSectionShadowDOM.querySelector("#sens_1");
        var sens2 = inputSection.inputSectionShadowDOM.querySelector("#sens_2");
        // submitButton.disabled = true;
        sens1.disabled = true;
        sens2.disabled = true;

    }

    makerButton(){
        if(inputSection.inputSectionShadowDOM.querySelector(".speed-input").checked == true){
            inputSection.inputSectionShadowDOM.querySelector(".speed-input").checked = false;
            inputSection.sendSpeed();
        }
        inputSection.uncheckOtherButtons(this);
        inputSection.inputSectionShadowDOM.querySelector(".maker-button").classList.toggle("btn-success");
        inputSection.inputSectionShadowDOM.querySelector(".speed-input").disabled = false;
        playersInMarket[otree.playerID]["strategy"] = "maker_2";
        // interactiveComponent.interactiveComponentShadowDOM.querySelector("information-table").updateState("bbo");;

        var makerBasicChangeMessage = {
            type: "role_change",
            state: playersInMarket[otree.playerID]["strategy"]
        };
        if(socketActions.socket.readyState === socketActions.socket.OPEN){
            console.log(JSON.stringify(makerBasicChangeMessage));
            socketActions.socket.send(JSON.stringify(makerBasicChangeMessage));
        }
        //s
        spreadGraph.removeArrows();
        spreadGraph.drawArrows();
        
        // var submitButton = inputSection.inputSectionShadowDOM.querySelector(".submit-button");
        var sens1 = inputSection.inputSectionShadowDOM.querySelector("#sens_1");
        var sens2 = inputSection.inputSectionShadowDOM.querySelector("#sens_2");
        // submitButton.disabled = false;
        sens1.disabled = false;
        sens2.disabled = false;

    }

    takerButton(){
        if(inputSection.inputSectionShadowDOM.querySelector(".speed-input").checked == true){
            inputSection.inputSectionShadowDOM.querySelector(".speed-input").checked = false;
            inputSection.sendSpeed();
        }
        inputSection.uncheckOtherButtons(this);
        inputSection.inputSectionShadowDOM.querySelector(".taker-button").classList.toggle("btn-success");
        inputSection.inputSectionShadowDOM.querySelector(".speed-input").disabled = false;
        playersInMarket[otree.playerID]["strategy"] = "taker";
        // interactiveComponent.interactiveComponentShadowDOM.querySelector("information-table").updateState("bbo");;

        // infoTable.updateRole("Taker");
        var algorithm2ChangeMessage = {
            type: "role_change",
            state: playersInMarket[otree.playerID]["strategy"]
        };
        if(socketActions.socket.readyState === socketActions.socket.OPEN){
            console.log(JSON.stringify(algorithm2ChangeMessage));
            socketActions.socket.send(JSON.stringify(algorithm2ChangeMessage));
        }
        spreadGraph.removeArrows();
        // var submitButton = inputSection.inputSectionShadowDOM.querySelector(".submit-button");
        var sens1 = inputSection.inputSectionShadowDOM.querySelector("#sens_1");
        var sens2 = inputSection.inputSectionShadowDOM.querySelector("#sens_2");
        // submitButton.disabled = false;
        sens1.disabled = false;
        sens2.disabled = false;

    }

    submitButton(){
        var sens1 = inputSection.inputSectionShadowDOM.querySelector("#sens_1");
        var sens2 = inputSection.inputSectionShadowDOM.querySelector("#sens_2");
        var sens1Value = sens1.value;
        var sens2Value = sens2.value;
        var algorithm2ChangeMessage = {
            type: "slider",
            a_x: sens1.value,
            a_y: sens2.value,
        };
        
        if(socketActions.socket.readyState === socketActions.socket.OPEN){
            console.log(JSON.stringify(algorithm2ChangeMessage));
            socketActions.socket.send(JSON.stringify(algorithm2ChangeMessage));
        }

        

    }

    outButton(){
        if(inputSection.inputSectionShadowDOM.querySelector(".speed-input").checked == true){
            inputSection.inputSectionShadowDOM.querySelector(".speed-input").checked = false;
            inputSection.sendSpeed();
        }
        inputSection.uncheckOtherButtons(this);
        inputSection.inputSectionShadowDOM.querySelector(".speed-input").disabled = true;
        inputSection.inputSectionShadowDOM.querySelector(".out-button").classList.toggle("btn-success");
        playersInMarket[otree.playerID]["strategy"] = "out";
        // interactiveComponent.interactiveComponentShadowDOM.querySelector("information-table").updateState("bbo");;

        // infoTable.updateRole("Out");
        spreadGraph.removeArrows();
       
        var outChangeMessage = {
            type: "role_change",
            state: playersInMarket[otree.playerID]["strategy"]
        };
        if(socketActions.socket.readyState === socketActions.socket.OPEN){
            console.log(JSON.stringify(outChangeMessage));
            socketActions.socket.send(JSON.stringify(outChangeMessage));
        }
        var sens1 = inputSection.inputSectionShadowDOM.querySelector("#sens_1");
        var sens2 = inputSection.inputSectionShadowDOM.querySelector("#sens_2");
        sens1.disabled = true;
        sens2.disabled = true;

    }

    sendSpeed(){
        var speedMsg = {
            type:"speed",
            speed: inputSection.inputSectionShadowDOM.querySelector(".speed-input").checked
        };
        if(socketActions.socket.readyState === socketActions.socket.OPEN){
            console.log(JSON.stringify(speedMsg));
            socketActions.socket.send(JSON.stringify(speedMsg));
        }
        var timeNow = profitGraph.getTime() - profitGraph.timeOffset;
        profitGraph.profitSegments.push(
            {
                startTime:timeNow,
                endTime:timeNow, 
                startProfit:profitGraph.profit, 
                endProfit:profitGraph.profit,
                state: playersInMarket[otree.playerID]["strategy"]
            }
        );

    }

    uncheckOtherButtons(button){
        
        if(playersInMarket[otree.playerID]["strategy"] == "maker_basic"){
            inputSection.inputSectionShadowDOM.querySelector(".manual-button").classList.toggle("btn-success");      
        }
        if(playersInMarket[otree.playerID]["strategy"] == "maker_2"){
            inputSection.inputSectionShadowDOM.querySelector(".maker-button").classList.toggle("btn-success");
        }
        if(playersInMarket[otree.playerID]["strategy"] == "taker"){
            inputSection.inputSectionShadowDOM.querySelector(".taker-button").classList.toggle("btn-success");
        }
        if(playersInMarket[otree.playerID]["strategy"] == "out"){
            inputSection.inputSectionShadowDOM.querySelector(".out-button").classList.toggle("btn-success");
        }
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

}
window.customElements.define('input-section', InputSection);