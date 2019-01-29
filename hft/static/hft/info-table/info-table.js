import {html,PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';

/*
 * This file defines the Info Table featured on the top of the main page using the Javascript Framework Polymer 3.0
 * 
 * The properties are the values that are information displayed to the user some are static (player_id) -
 * while others are dynamic (profit,spread_value)
 *
 * If you want to change a value on the table use: - 
 * document.querySelector('info-table').setAttribute("info_variable","info"); 
 *
 * This changes the value of player_role to Maker once the user presses the Maker button
 * document.querySelector('info-table').setAttribute("player_role","Maker"); 
*/
class InfoTable extends PolymerElement {
  constructor(){
    super();
    interactiveComponent.infoTableDOM = interactiveComponent.interactiveComponentShadowDOM.querySelector("info-table");
    interactiveComponent.infoTableDOM.attachShadow({mode: 'open'});

    infoTable.infoTableShadowDOM = interactiveComponent.infoTableDOM.shadowRoot;
    infoTable.infoTableShadowDOM.innerHTML = `<style>
    table{
      border-right:solid 1px rgb(200,200,200);
      text-align:left;
      width:100%;
      height:100%;
    }
    td{
      margin-top:10px; 
      margin-left:50%;
    }
    .bold{
      font-weight:bold;
    }
  </style>
          <table>
            <tr>
              <td class="info_text"><span class="bold">Period</span>: <span class="period_id"></span>                  </td>
  
              <td class="info_text"><span class="bold">Role</span>: <span class="player_role"></span>                </td>
            </tr>
            <tr>
              <td class="info_text"><span class="bold">Number of Traders</span>: <span class="num_traders"></span>    </td>  
              <td class="info_text"><span class="bold">Number of Makers</span>: <span class="num_makers"></span>       </td>
            </tr>
            <!-- Row 1 of info box -->
            <tr>
              <td class="info_text"><span class="bold">Your Bid</span>:     <span class="user_bid"></span>         , <span class="bold">Your Offer</span>: <span class="user_offer"></span></td>
              <td class="info_text"><span class="bold">Your Profit</span>:  <span class="profit"></span>              </td> 
            </tr>
            <!-- Row 3 of info box -->
            <tr>
              <td class="info_text"><span class="bold">Best Bid</span>: <span class="curr_bid"></span>       </td>
              <td class="info_text"><span class="bold">Best Offer</span>: <span class="curr_ask"></span>       </td>
            </tr>
        </table>
    `;
    
    infoTable.updateProfit = this.updateProfit;
    infoTable.updateBidAndAsk = this.updateBidAndAsk;
    infoTable.updateRole = this.updateRole;
    infoTable.updateUserBidAndAsk = this.updateUserBidAndAsk;
    infoTable.init = this.init;
    
  }
  updateRole(role){
    infoTable.infoTableShadowDOM.querySelector(".player_role").innerHTML = role;
  }
  updateProfit(profit){
    infoTable.infoTableShadowDOM.querySelector(".profit").innerHTML = profit * 1e-4;
  }
  updateBidAndAsk(bid,ask){
    spreadGraph.bestBid = bid;
    spreadGraph.bestOffer = ask;

    //If we use polymer then update property and use these lines of code in the observer function
    infoTable.infoTableShadowDOM.querySelector(".curr_bid").innerHTML = bid * 1e-4;
    infoTable.infoTableShadowDOM.querySelector(".curr_ask").innerHTML = ask * 1e-4;
    // document.querySelector('info-table').user_bid = price;

    // document.querySelector('info-table').user_offer = price;
  }
  updateUserBidAndAsk(price,side){
    if(side == "B"){
      infoTable.infoTableShadowDOM.querySelector(".user_bid").innerHTML = price * 1e-4;
    } else if(side == "S"){
      infoTable.infoTableShadowDOM.querySelector(".user_offer").innerHTML = price * 1e-4;
    }
  }

}
window.customElements.define('info-table', InfoTable);