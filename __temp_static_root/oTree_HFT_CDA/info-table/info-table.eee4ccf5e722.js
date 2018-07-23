import {html, PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';
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
          table-layout : auto;
          
        }
        td{
          margin-top:10px; 
          text-align:center;
          margin-left:50%;
        }
      </style>
      
      <table>
        <b>
        <!-- Row 1 of info box -->
        <tr>
            <td class="info_text">Player ID:            [[player_id]]   </td>
            <td class="info_text">Number of Traders:    [[num_traders]] </td>
            <td class="info_text">Role:                 [[player_role]] </td>
            <td class="info_text">Fundamental Value:    [[fp]]          </td>
        </tr>
        <!-- Row 2 of info box -->
        <tr>
            <td class="info_text">Period:               [[period_id]]    </td>
            <td class="info_text">Number of Makers:     [[num_makers]]   </td>
            <td class="info_text">Spread:               [[spread_value]] </td>
            <td class="info_text">Current Buy Offer:    [[curr_bid]]     </td>
        </tr>
        <!-- Row 3 of info box -->
        <tr>
            <td class="info_text">Speed Cost:           [[speed_cost]]   </td>
            <td class="info_text">Your Profit:          [[profit]]       </td>
            <td class="info_text">Current Sell Offer:   [[curr_ask]]     </td>
        </tr>
      </b>
    </table>
    `;
  }

  static get properties() {
    return {
      player_id: {
        type: String
        value:"N/A"
      },
      num_traders: {
        type: String,
        value:" "
      },
      player_role: {
        type: String,
        value:" "
      },
      fp: {
        type: String,
        value:" "
      },

      period_id: {
        type: String,
        value:" "
      },
      num_makers: {
        type: String,
        value:" "
      },
      spread_value: {
        type: String,
        value:" "
      },
      curr_bid: {
        type: String,
        value:" "
      },

      speed_cost: {
        type: String,
        value:" "
      },
      num_snipers: {
        type: String,
        value:" "
      },
      profit: {
        type: String,
        value:" "
      },
      curr_ask: {
        type: String,
        value:" "
      }
    };
  }
}
window.customElements.define('info-table', InfoTable);