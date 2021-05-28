import {html,PolymerElement} from '../node_modules/@polymer/polymer/polymer-element.js';

/*
 * A single cell on the results page
 *
 * Pie chart cannibalized from https://www.highcharts.com/demo/pie-legend
 */
export class ResultsCell extends PolymerElement {
  constructor(){
    super();
  }

  static get template() {
    return html `
    <style>
      .outer {
        display: flex;
        justify-content: space-around;
        padding: 5px;
      }
      .data {
        display: inline-block;
        margin: 4px;
      }
      h2 {
	margin: 2%;
      }
    </style>

    <div style="text-align:center; padding:10px;" class="wrapper" id="parent">
      <h2>[[ name ]]</h2>
      <!--
      <table style="display:inline-block; text-align:center;">
        <tr>
          <td style="display:inline-block;">
            <div id="container" class="container"></div>
          </td>
          <td style="display:inline-block;">
            <div id="container3" class="container3"></div>
          </td>
          <td style="display:inline-block; margin=10px;">
            <div id="container2" class="container"></div>
          </td>

        </tr>
      </table> -->
      <div class="outer">
        <div id="container" class="container"></div>
        <div id="container3" class="container3"></div>
        <div id="container2" class="container"></div>
      </div>
      <div style="display:flex;">
        <div style="flex:1; text-align:center;">
          <strong>Payoff:</strong>
          <span>[[toFixed(net)]]</span>
        </div>
        <div style="flex:1; text-align:center;">
          <span>Average Sensitivity of Algorithms</span>
          <hr style="width: 60%">
          <span class="data"><strong>Inventory:</strong> [[ invSensitivity ]]</span>
          <span style$="display: [[_signedVolumeDisplay()]];" class="data"><strong>Signed Volume:</strong> [[ signedVolume ]]</span>
          <span class="data"><strong>External Feed:</strong> [[ externalFeed ]]</span>
        </div>
      </div>
    </div>
    `;
  }

  connectedCallback() {
    super.connectedCallback();
    const strategies = this.strategies;
    let strategiesData = [];
    for(let key in strategies) {
      strategiesData.push({
        name: key,
        y: strategies[key]
      })
    }
    console.log(strategiesData)

    const speedUsage = this.speedUsage;
    console.log(speedUsage)
    let speedData = [];
    for(let key in speedUsage) {
      speedData.push({
        name: key,
        y: speedUsage[key]
      })
    }
    console.log(speedData)

    //let lowVal = Math.min(this.width, this.height);
    //let width = lowVal;
    //let height = lowVal;
    let width = this.width;
    let height = this.height;
    const parentStyle = "text-align:center; line-height:10px; width:" + width + "px; height:" + height + "px";
    width = width/2.5;
    height = height/1.4;
    let containerStyle = "width:" + width + "px; height:" + height + "px";
    this.$.parent.setAttribute("style", parentStyle);
    this.$.container.setAttribute("style", containerStyle);
    this.$.container2.setAttribute("style", containerStyle);
    this.$.container3.setAttribute("style", containerStyle);

    const gross = this.net + this.tax + this.speedCost;

    let chart1 = Highcharts.chart(this.$.container, {
      chart: {
        plotBackgroundColor: null,
        plotBorderWidth: null,
        plotShadow: false,
        type: 'pie',
        size: '100%',
        spacingLeft: 0,
        spacingRight: 0
      },
      title: {
        text: 'Strategies'
      },
      tooltip: {
        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
      },
      credits: {
        enabled: false
      },
      plotOptions: {
        pie: {
          allowPointSelect: true,
          cursor: 'pointer',
          dataLabels: {
            enabled: false,
            padding: 0
          },
          showInLegend: false
        }
      },
      series: [{
        name: 'Strategies',
        colorByPoint: true,
        data: strategiesData
      }]
    });

    let chart2 = Highcharts.chart(this.$.container2, {
      chart: {
        type: 'columnrange',
      },
      title: {
        text: 'Payoff'
      },
      xAxis: {
        categories: [" "],
        labels: {
          enabled: false,
        },
      },
      yAxis: {
        title: {
          text: ''
        }
      },
      plotOptions: {
        columnrange: {
          pointPadding: 0,
          groupPadding: 0,
          borderWidth: 0,
          shadow: false
        },
      },
      credits: {
        enabled: false
      },
      tooltip: {
        enabled: false,
      },
      series: [
      {
        name: "Payment Before Deduction",
        data: [
          [0, gross]
        ],
        showInLegend: true,
      },
      {
        name: "Deduction",
        data: [
          [gross-this.tax, gross]
        ],
        showInLegend: true,
        color: '#DD0000'
      },
      {
        name: "Payoff",
        data: [
          [0, this.net - this.speedCost]
        ],
        showInLegend: true,
      },
      ]
    });
    
    let chart3 = Highcharts.chart(this.$.container3, {
      chart: {
        plotBackgroundColor: null,
        plotBorderWidth: null,
        plotShadow: false,
        type: 'pie',
        size: '100%',
        spacingLeft: 0,
        spacingRight: 0
      },
      title: {
        text: 'Speed Usage'
      },
      tooltip: {
        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
      },
      credits: {
        enabled: false
      },
      plotOptions: {
        pie: {
          allowPointSelect: true,
          cursor: 'pointer',
          dataLabels: {
            enabled: false,
            padding: 0
          },
          showInLegend: false
        }
      },
      series: [{
        name: 'Speed Usage',
        colorByPoint: true,
        data: speedData
      }]
    });
    
    

    chart1.setSize();
    chart2.setSize();
    chart3.setSize();
    chart1.reflow();
    chart2.reflow();
    chart3.reflow();
  }

  static get properties() {
    return {
      strategies: {
        type: Object,
        //value: {the:10, value:20}
      },
      speedUsage: {
        type: Object,
        //value: {the:10, value:20}
      },
      net: {
        type: Number,
      },
      tax: {
        type: Number,
      },
      speedCost: {
        type: Number,
      },
      name: {
        type: String,
        //value: "Sample Name"
      },
      invSensitivity: {
        type: Number,
        //value: 5.1
      },
      signedVolume: {
        type: Number,
        //value: 3.7
      },
      externalFeed: {
        type: Number,
        //value: 4.0
      },
      width: {
        type: Number,
        //value: 300
      },
      height: {
        type: Number,
        //value: 300
      },
      subscriptionTime: {
        type: Number,
      },
    }
  }

  _signedVolumeDisplay() {
    return OTREE_CONSTANTS.svSliderDisplayed ? 'default' : 'none';
  }

  toFixed(num) {
    return num.toFixed(2);
  }

}

window.customElements.define('results-cell', ResultsCell);
