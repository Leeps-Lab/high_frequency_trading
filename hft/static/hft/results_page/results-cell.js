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
        height: 100%;
      }
      .data {
	      display: inline-block;
      }
      .data_box {
        text-align: center;
        margin: 3px;
        border: 1px solid black;
        padding: 4px
      }
      .wrapper {
        text-align:center;
        padding:3px;
        position: relative;
      }
      h2 {
	      margin: 2%;
      }
    </style>

    <div class="wrapper" id="parent">
      <h2>[[ name ]]</h2>
      <div class="outer">
        <div>
          <div id="container" class="container"></div>
          <div class="data_box">
            <span>Average Sensitivities</span>
            <hr style="width: 60%">
            <span class="data"><strong>Inventory:</strong> [[ invSensitivity ]]</span>
            <span class="data"><strong>External Feed:</strong> [[ externalFeed ]]</span>
          </div>
        </div>
        <div id="container2" class="container"></div>
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

    const payoff = this.net;
    let payoffData = [];
    payoffData.push(payoff);

    const tax = this.tax;
    let taxData = [];
    taxData.push(tax);

    const speed = this.speed;
    let speedData = []
    speedData.push(speed);

    //let lowVal = Math.min(this.width, this.height);
    //let width = lowVal;
    //let height = lowVal;
    let width = this.width;
    let height = this.height;
    let height2;
    const parentStyle = "text-align:center; line-height:10px; width:" + width + "px; height:" + height + "px";
    width = width/2.5;
    height = height/1.4;
    height2 = this.height/1.1;
    let containerStyle = "width:" + width + "px; height:" + height + "px";
    let container2Style = "width:" + width + "px; height:" + height2 + "px";
    this.$.parent.setAttribute("style", parentStyle);
    this.$.container.setAttribute("style", containerStyle);
    this.$.container2.setAttribute("style", container2Style);

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
            enabled: true,
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
        type: 'column',
        size: '100%'
      },
      title: {
        text: 'Payoff'
      },
      xAxis: {
        categories: [" "],
        crosshair: true
      },
      yAxis: {
        max: 200,
        min: -100,
        title: {
          text: ''
        }
      },
      credits: {
        enabled: false
      },
      plotOptions: {
        column: {
          stacking: 'normal',
          pointPadding: 0,
          groupPadding: 0,
          borderWidth: 0,
          allowPointSelect: true,
          cursor: 'pointer',
          dataLabels: {
            enabled: true
          },
          showInLegend: true
        }
      },
      series: [{
        name: "Net Payoff",
        data: payoffData,
        showInLegend: true,
        index: 2
      },
      {
        name: "Tax",
        data: taxData,
        showInLegend: true,
        index: 1,
        color: '#FF0000'
      },
      {
        name: "Speed",
        data: speedData,
        showInLegend: true,
        index: 0,
        color: '#FFA500'
      }
      ]
    });

    chart1.setSize();
    chart2.setSize();
    chart2.reflow();
  }

  static get properties() {
    return {
      strategies: {
        type: Object,
        //value: {the:10, value:20}
      },
      net: {
        type: Number,
      },
      tax: {
        type: Number,
      },
      speed: {
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
      }
    }
  }

}

window.customElements.define('results-cell', ResultsCell);
