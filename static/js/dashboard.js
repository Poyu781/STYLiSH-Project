/* eslint-disable no-undef */

function Dashboard(data) {
    this.data = data;

    this.onlineUserCount = function() {
        const dom = document.getElementById('number');
        dom.innerHTML = 'Total Revenue: ' + data.totalRevenue;
    };

    this.drawProductsDivideByColor = function() {
        var colorData = [{
            values: data.productsDivideByColor.map(x => parseInt((x.count).replace(',',''))),
            labels: data.productsDivideByColor.map(x => x.color_name),
            marker: {
                colors: data.productsDivideByColor.map(x => x.color_code)
            },
            type: 'pie'
        }];
        // console.log(colorData)
        var layout = {
            title: {
                text:'Product sold percentage in different colors',
            },
            height: 350,
        };
        console.log(colorData)
        Plotly.newPlot('pie', colorData, layout);
    };

    this.drawProductsInPriceRange = function() {
        var trace = {
            x: this.data.productsInPriceRange,
            type: 'histogram',
        };
        var layout = {
            title: {
                text:'Product sold quantity in different price range',
            },
            xaxis: {
                title: {
                    text: 'Price Range',
                },
            },
            yaxis: {
                title: {
                    text: 'Quantity',
                }
            }
        };
        var data = [trace];
        Plotly.newPlot('histogram', data, layout);
    };

    this.drawTop5ProductsDividedBySize = function() {
        var sizeData = this.data.top5ProductsDividedBySize.map(d => ({
            x: d.ids.map(id => 'product ' + id),
            y: d.count,
            name: d.size,
            type: 'bar'
        }));
        // console.log(sizeData)
        var layout = {
            barmode: 'stack',
            title: {
                text:'Quantity of top 5 sold products in different sizes',
            },
            yaxis: {
                title: {
                    text: 'Quantity',
                }
            }
        };
        Plotly.newPlot('bar', sizeData, layout);
    };
}
