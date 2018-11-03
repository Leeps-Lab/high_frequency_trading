import html, PolymerElement from '../node_modules/@polymer/polymer/polymer-element.js';

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
  static get template() {
    return html`
<style>
  table{
    width:100%;
    border: rgb(200, 200, 200) 3px solid;
    text-align:center;
    table-layout : auto;
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
          <!-- Row 1 of info box -->
          <tr>
              <td class="info_text"><span class="bold">Player ID</span>:            [[player_id]]   </td>
              <td class="info_text"><span class="bold">Role</span>:                 [[player_role]] </td>
              <td class="info_text"><span class="bold">Fundamental Value</span>:    [[fp]]          </td>
              <td class="info_text"><span class="bold">Spread</span>:               [[spread_value]] </td>
          </tr>
          <!-- Row 2 of info box -->
          <tr>
              <td class="info_text"><span class="bold">Group ID</span>:             [[group_id]]       </td>
              <td class="info_text"><span class="bold">Number of Traders</span>:    [[num_traders]] </td>
              <td class="info_text"><span class="bold">Speed Cost</span>:           [[speed_cost]]   </td>      
              <td class="info_text"><span class="bold">Current Buy Offer</span>:    [[curr_bid]]     </td>
          </tr>
          <!-- Row 3 of info box -->
          <tr>
              <td class="info_text"><span class="bold">Period</span>:               [[period_id]]    </td>
              <td class="info_text"><span class="bold">Number of Makers</span>:     [[num_makers]]   </td>
              <td class="info_text"><span class="bold">Your Profit</span>:          [[profit]]       </td>
              <td class="info_text"><span class="bold">Current Sell Offer</span>:   [[curr_ask]]     </td>
          </tr>
      </table>
    `;
  }

  static get properties() {
    return {
      player_id: {
        type: String
      },
      num_traders: {
        type: String, 
      },
      group_id: {
        type: String, 
      },
      player_role: {
        type: String,
      },
      fp: {
        type: String,
      },

      period_id: {
        type: String,
      },
      num_makers: {
        type: String,
      },
      spread_value: {
        type: String,
      },
      curr_bid: {
        type: String,
      },
      speed_cost: {
        type: String,
      },
      num_snipers: {
        type: String,
      },
      profit: {
        type: String,
      },
      curr_ask: {
        type: String,
      }
    };
  }
}
window.customElements.define('info-table', InfoTable);