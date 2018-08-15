
document.getElementById("maker").onclick = function () {
    if ((document.getElementById("maker").className == "button-off") && (document.getElementById("maker").className != "button-pressed")){
        //IF BUTTON IS NOT PRESSED OR ON THEN TURN IT ON AFTER DELAD (Button_Pressed())
        $("#maker").toggleClass('button-off button-pressed');
        $('#player_role').html('MAKER');

        document.getElementById("speed-btn").disabled = false;

        var timeNow = getTime() - graph.timeOffset;
        graph.profitSegments.push(
            {
                startTime:timeNow,
                endTime:timeNow, 
                startProfit:graph.profit, 
                endProfit:graph.profit,
                state:$("#player_role").text()
            }
        );


        var msg = {
            type: 'role_change',
            id: {{player.id}},
            id_in_group: {{player.id_in_group}},
            state: "MAKER"
        };
        if (socket.readyState === socket.OPEN) {
          socket.send(JSON.stringify(msg));
        }

        Button_Pressed("maker");

    }
    $("#out").attr('class', 'button-off');
    $("#sniper").attr('class', 'button-off');
};

document.getElementById("sniper").onclick = function () {
    if ((document.getElementById("sniper").className == "button-off") && (document.getElementById("sniper").className != "button-pressed")){
        //IF BUTTON IS NOT PRESSED OR ON THEN TURN IT ON AFTER DELAD (Button_Pressed())
        $("#sniper").toggleClass('button-off button-pressed');
        $('#player_role').html('SNIPER');

        document.getElementById("speed-btn").disabled = false;


        var timeNow = getTime() - graph.timeOffset;
        graph.profitSegments.push(
            {
                startTime:timeNow,
                endTime:timeNow, 
                startProfit:graph.profit, 
                endProfit:graph.profit,
                state:$("#player_role").text()
            }
        );

        var msg = {
            type: 'role_change',
            id: {{player.id}},
            id_in_group: {{player.id_in_group}},
            state: "SNIPER"
        };
        if (socket.readyState === socket.OPEN) {
            socket.send(JSON.stringify(msg));
        }
        Button_Pressed("sniper");

        Spread_Graph.clear();
        delete spread_lines[parseInt($("#player_id").text())]

    }

    $("#maker").attr('class', 'button-off');
    $("#out").attr('class', 'button-off');
};

//OUT BUTTON
document.getElementById("out").onclick = function () {
    if (document.getElementById("out").className == "button-off"){
        //IF THE BUTTON IS OFF TURN IT ON WITH NO DELAY
        $("#out").toggleClass('button-off button-on');
        $('#player_role').html('OUT');
        document.getElementById("speed-btn").disabled = true;
        
        
        var timeNow = getTime() - graph.timeOffset;
        graph.profitSegments.push(
            {
                startTime:timeNow,
                endTime:timeNow, 
                startProfit:graph.profit, 
                endProfit:graph.profit,
                state:$("#player_role").text()
            }
        );

        var msg = {
            type: 'role_change',
            id: {{player.id}},
            id_in_group: {{player.id_in_group}},
            state: "OUT"
        };
        if (socket.readyState === socket.OPEN) {
            socket.send(JSON.stringify(msg));
        }
        Button_Pressed("out");
        
        if(speed){
            updatespeed();
            document.getElementById("speed-btn").checked = false;
        }

        Spread_Graph.clear();
        delete spread_lines[parseInt($("#player_id").text())]

    }

    $("#maker").attr('class', 'button-off');
    $("#sniper").attr('class', 'button-off');
};

var button_timer;
var graph_timer;
function Button_Pressed(id_name){
    //Wait .5 seconds for button pressed to even for fast players
    // to eliminate spam clicking
    button_timer = setTimeout(Button_Change.bind(null,id_name),500);
}
function Button_Change(id_name){
    //TURNING BUTTON ON
    if(id_name == "out" || id_name == "maker"){
        $("#"+id_name).toggleClass('button-pressed button-on');
    }else if (id_name == "sniper"){
        $("#"+id_name).toggleClass('button-pressed button-on-sniper');

    }
}