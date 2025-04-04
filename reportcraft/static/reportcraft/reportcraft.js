'use strict';


const figureTypes = [
    "histogram", "lineplot", "barchart", "scatterplot", "pie", "gauge", "timeline", "columnchart",
    "plot", "histo", "bar", 'geochart'
];

const ColorSchemes = {
    Accent: ['#7fc97f', '#beaed4', '#fdc086', '#ffff99', '#386cb0', '#f0027f', '#bf5b17', '#666666'],
    Category10: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
    Dark2: ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#666666'],
    Live16: ['#67aec1', '#c45a81', '#cdc339', '#ae8e6b', '#6dc758', '#a084b6', '#667ccd', '#cd4f55', '#805cd6', '#cf622d', '#a69e4c', '#9b9795', '#6db586', '#c255b6', '#073b4c', '#ffd166'],
    Live4: ['#8f9f9a', '#c56052', '#9f6dbf', '#a0b552'],
    Live8: ['#073b4c', '#06d6a0', '#ffd166', '#ef476f', '#118ab2', '#7f7eff', '#afc765', '#78c5e7'],
    Observable10: ['#4269d0', '#efb118', '#ff725c', '#6cc5b0', '#3ca951', '#ff8ab7', '#a463f2', '#97bbf5', '#9c6b4e', '#9498a0'],
    Paired: ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928'],
    Pastel1: ['#fbb4ae', '#b3cde3', '#ccebc5', '#decbe4', '#fed9a6', '#ffffcc', '#e5d8bd', '#fddaec', '#f2f2f2'],
    Pastel2: ['#b3e2cd', '#fdcdac', '#cbd5e8', '#f4cae4', '#e6f5c9', '#fff2ae', '#f1e2cc', '#cccccc'],
    Set1: ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999'],
    Set2: ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3'],
    Set3: ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd', '#ccebc5', '#ffed6f'],
    Tableau10: ['#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab'],

    // https://observablehq.com/@d3/color-schemes
    // Sequential colors
    Blues: d3.schemeBlues[9],
    Greens: d3.schemeGreens[9],
    Greys: d3.schemeGreys[9],
    Oranges: d3.schemeOranges[9],
    Purples: d3.schemePurples[9],
    Reds: d3.schemeReds[9],
    BuGn: d3.schemeBuGn[9],
    BuPu: d3.schemeBuPu[9],
    GnBu: d3.schemeGnBu[9],
    OrRd: d3.schemeOrRd[9],
    PuBu: d3.schemePuBu[9],
    PuRd: d3.schemePuRd[9],
    RdPu: d3.schemeRdPu[9],
    YlGn: d3.schemeYlGn[9],
    YlGnBu: d3.schemeYlGnBu[9],
    YlOrBr: d3.schemeYlOrBr[9],
    YlOrRd: d3.schemeYlOrRd[9],
    PuBuGn: d3.schemePuBuGn[9],
};

const styleTemplate = _.template('<%= selector %> { <%= rules %> }');
const contentTemplate = _.template(
    '<div id="entry-<%= id %>" <% let style = entry.style || ""; %> class="section-entry <%= style %>" >' +
    '   <% if ((entry.title) && ((!entry.kind) || (entry.kind === "richtext")))  { %>' +
    '       <h4><%= entry.title %></h4>' +
    '   <% } %>' +
    '   <% if (entry.description) { %>' +
    '       <div class="description"><%= renderMarkdown(entry.description) %></div>' +
    '   <% } %>' +
    '   <% if (entry.text) { %>' +
    '       <div class="rich-text"><%= renderMarkdown(entry.text) %></div>' +
    '   <% } %>' +
    '   <% if ((entry.kind === "table") && (entry.data)) { %>' +
    '       <%= tableTemplate({id: id, entry: entry}) %>' +
    '   <% } else if (figureTypes.includes(entry.kind)) { %>' +
    '       <figure id="figure-<%= entry.id || id %>" data-type="<%= entry.kind %>" data-chart="<%= encodeObj(entry) %>" >' +
    '       </figure>' +
    '   <% }%>' +
    '   <% if (entry.notes) { %>' +
    '       <div class="notes"><%= renderMarkdown(entry.notes) %></div>' +
    '   <% } %>' +
    '</div>'
);

const sectionTemplate = _.template(
    '<section id="section-<%= id %>" <% let style = section.style || "row"; %>' +
    '       class="<%= style %>">' +
    '       <%  if (section.title)  {%>' +
    '       <h3 class="section-title col-12"><%= section.title %></h3>' +
    '       <% } %>' +
    '       <%  if (section.description)  {%>' +
    '       <div class="description col-12"><%= renderMarkdown(section.description) %></div>' +
    '       <% } %>' +
    '     <% _.each(section.content, function(entry, j){ %><%= contentTemplate({id: id+"-"+j, entry: entry}) %><% }); %>' +
    '</section>'
);

const tableTemplate = _.template(
    '<table id="table-<%= id %>" class="table table-sm table-hover">' +
    '<% if (entry.title) { %>' +
    '   <caption class="text-center"><%= entry.title %></caption>' +
    '<% } %>' +
    '<% if (entry.header.includes("row")) { %>' +
    '   <thead><tr>' +
    '       <% _.each(entry.data[0], function(cell, i){ %>' +
    '       <th><%= cell %></th>' +
    '       <% }); %>' +
    '   </tr></thead>' +
    '<% } %>' +
    '<tbody>' +
    '<% _.each(entry.data, function(row, j){ %>' +
    '   <% if ((!entry.header.includes("row")) || (j>0)) { %>' +
    '       <tr>' +
    '       <% _.each(row, function(cell, i){ %>' +
    '           <% if (entry.header.includes("column") && (i==0)) { %>' +
    '               <th><%= cell %></th>' +
    '           <% } else { %>' +
    '               <td><%= cell %></td>' +
    '           <% } %>' +
    '       <% }); %>' +
    '       </tr>' +
    '   <% } %>' +
    '<% }); %>' +
    '</tbody>' +
    '</table>'
);

const NUM_TICKS = 10;

function renderMarkdown(text) {
    let markdown = new showdown.Converter();
    return markdown.makeHtml(text);
}

function getPrecision(row, steps) {
    steps = steps || 8;
    let diff = (row[row.length - 1] - row[0]) / steps;
    return Math.abs(Math.floor(Math.log10(diff.toPrecision(1)) || 2))
}

function encodeObj(obj) {
    // encode object as base64 string
    const utf8Bytes = encodeURIComponent(JSON.stringify(obj)).replace(/%([0-9A-F]{2})/g,
        function toSolidBytes(match, p1) {
            return String.fromCharCode('0x' + p1);
        });
    return btoa(utf8Bytes);
}

function decodeObj(base64Str) {
    // decode base64 string to object
    const binaryString = atob(base64Str);
    const percentEncodedStr = binaryString.split('').map(function (c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join('');
    return JSON.parse(decodeURIComponent(percentEncodedStr));
}


function drawXYChart(figure, chart, options, type = 'spline') {
    migrateXYData(chart);
    let data = Object.fromEntries(chart.data.map(item => [item[0], item.slice(1)]));

    let series = [];
    let columns = [];
    let axes = {};
    let data_type = type;
    let spline_opts = {interpolation: {}};
    let axis_opts = {x: {}, y: {}, y2: {}};

    let xdata = [];
    let xmin = Math.min(...data[chart.x]);
    let xmax = data[chart.x].slice(-1)[0];
    let xscale = d3.scaleLinear().domain([xmin, xmax]);
    let tick_values = xscale.ticks(NUM_TICKS);
    let prec = chart['x-tick-precision'];

    if (prec == null) {
        prec = getPrecision(tick_values);
    }

    // conversion functions,
    let xfwd = function (x) {
        return x
    };
    let xbwd = function (x) {
        return x
    };

    // X-axis scale
    switch (chart['x-scale']) {
        case 'time':
            xfwd = function (x) {
                return Date.parse(x)
            };
            axis_opts.x = $.extend(axis_opts.x, {
                type: 'timeseries',
                tick: {format: chart['time-format'], culling: {max: 13}}
            });
            break;
        case 'pow':
        case 'inv-square':
            let mult = (chart['x-scale'] === 'pow') ? 1 : -1;
            xfwd = d3.scalePow().exponent(mult * 2).domain([xmin, xmax]);
            xbwd = xfwd.invert;

            xscale.domain([xfwd(xmin), xfwd(xmax)]);
            tick_values = xscale.ticks(NUM_TICKS);

            prec = getPrecision(tick_values);
            axis_opts.x = $.extend(axis_opts.x, {
                tick: {
                    values: tick_values,
                    multiline: false,
                    format: x => xbwd(x).toFixed(prec)
                }
            });
            break;
        case 'log':
            xfwd = d3.scaleLog().domain([xmin, xmax]);
            xbwd = xfwd.invert;
            xscale.domain([xfwd(xmin), xfwd(xmax)]);
            tick_values = xscale.ticks(NUM_TICKS);
            prec = getPrecision(tick_values);
            axis_opts.x = $.extend(axis_opts.x, {
                tick: {
                    values: tick_values,
                    multiline: false,
                    format: x => xbwd(x).toFixed(prec)
                }
            });
            break;
        case 'identity':
            axis_opts.x = $.extend(axis_opts.x, {
                type: 'index',
                tick: {
                    multiline: false,
                }
            });
            break;
        default:    // linear
            axis_opts.x = $.extend(axis_opts.x, {
                tick: {
                    values: tick_values,
                    fit: true,
                    multiline: false,
                    format: x => xbwd(x).toFixed(prec)
                }
            });
    }

    // Axis limits
    if (chart['x-limits']) {
        axis_opts.x = $.extend(axis_opts.x, {
            min: xfwd(chart['x-limits'][0]),
            max: xfwd(chart['x-limits'][1]),
            padding: 0,
        });
    }
    if (chart['y1-limits']) {
        axis_opts.y = $.extend(axis_opts.y, {
            min: chart['y1-limits'][0],
            max: chart['y1-limits'][1],
            padding: 0,
        });
    }
    if (chart['y2-limits']) {
        axis_opts.y2 = $.extend(axis_opts.y2, {
            min: chart['y2-limits'][0],
            max: chart['y2-limits'][1],
            padding: 0,
        });
    }

    // Spline Plo type
    if (["cardinal", "basis", "step", "step-before", "step-after"].includes(chart['interpolation'])) {
        data_type = 'spline';
        spline_opts.interpolation.type = chart['interpolation'];
    }


    // convert x values
    xdata = [chart.x, ...(data[chart.x].map(xfwd))];
    axis_opts.x.label = chart["x-label"] || chart.x;
    columns.push(xdata);

    // remove raw data from dom, not needed anymore
    figure.removeData('chart').removeAttr('data-chart');

    // gather y1 columns data and configure labels and color
    $.each(chart.y1, function (i, line) {  // y1
        columns.push([line, ...data[line]]);
        axes[line] = 'y';
        series.push(line);
        if (i === 0) {
            axis_opts.y.label = chart["y1-label"] || line;
        }
    });

    // gather y2 axes data
    $.each(chart.y2, function (i, line) {  // y2
        columns.push([line, ...data[line]]);
        axes[line] = 'y2';
        series.push(line);
        axis_opts.y2.show = true;
        if (i === 0) {
            axis_opts.y.label = chart["y2-label"] || line;
        }
    });

    let color_scale = d3.scaleOrdinal().domain(series).range(options.scheme);
    $.each(series, function (i, key) {
        if (!(key in options.colors)) {
            options.colors[key] = color_scale(key);
        }
    });

    let c3chart = c3.generate({
        bindto: `#${figure.attr('id')}`,
        size: {width: options.width, height: options.height},
        data: {
            type: data_type,
            columns: columns,
            colors: options.colors,
            axes: axes,
            x: chart.x,
        },
        spline: spline_opts,
        point: {show: (data[chart.x].length < 15)},
        axis: axis_opts,
        grid: {y: {show: true}},
        //zoom: {enabled: true, type: 'drag'},
        onresize: function () {
            this.api.resize({
                width: figure.width(),
                height: figure.width() * options.height / options.width
            });
        }
    });
    if (chart.annotations) {
        c3chart.xgrids(chart.annotations)
    }
    figure.data('c3-chart', c3chart);
}

function migrateData(chart) {
    // convert v2 data to v3 format
    if (!Array.isArray(chart.data)) {
        let data = chart.data;
        for (let key in data) {
            if (data.hasOwnProperty(key)) {
                chart[key] = data[key];
            }
        }
    }
}

function migrateXYData(chart) {
    // convert v2 data to v3 format
    if (!Array.isArray(chart.data)) {
        let info = chart.data;
        chart.data = [info.x, ...info.y1];
        if (Array.isArray(info.y2)) {
            chart.data.push(...info.y2);
        }
        chart.x = info.x[0];
        chart.y1 = info.y1.map(item => item[0]);
        chart.y2 = info.y2.map(item => item[0]);

        delete info.x;
        delete info.y1;
        delete info.y2;

        for (let key in info) {
            if (info.hasOwnProperty(key)) {
                chart[key] = info[key];
            }
        }
    }
}

function drawBarChart(figure, chart, options) {
    let series = [];
    let flavors = [];
    let hidden = [];

    // migrate data
    migrateData(chart);

    let colorfunc = function (color, d) {
        return color;
    };

    // remove raw data from dom
    figure.removeData('chart');
    figure.removeAttr('data-chart');

    // series names and alternate groupings
    $.each(chart["data"][0], function (key, value) {
        if (key === chart["color-by"]) {
            // hide series since it will be used for coloring
            hidden.push(key);
        } else if (key === chart["x-label"]) {
            // ignore x-axis series
        } else {
            // new series
            series.push(key);
        }
    });

    // names for coloring using "color-by" field
    if (chart["color-by"]) {
        let key = chart["color-by"];
        $.each(chart["data"], function (i, item) {
            if (!(flavors.includes(item[key]))) {
                flavors.push(item[key])
            }
        });

        // update color function for color-by
        colorfunc = function (color, d) {
            if (typeof d === "object") {
                let flavor = chart['data'][d.index][key];
                return options.colors[flavor];
            } else {
                return color;
            }
        }
    }
    // update color dictionary
    let color_scale = d3.scaleOrdinal().domain(flavors.concat(series)).range(options.scheme);
    $.each(series, function (i, key) {
        if (!(key in options.colors)) {
            options.colors[key] = color_scale(key);
        }
    });

    function formatKilo(num) {
        return num >= 1000 ? (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K' : num.toString();
    }

    let line_axes = {};
    let line_types = {};
    let axis_y2 = {show: chart['line'] && true || false, label: chart['line']};
    let x_ticks = {
        culling: {'max': chart["x-culling"] || false},
        multiline: chart["wrap-x-labels"] || false,
    };

    if (chart['line']) {
        line_types[chart['line']] = "line";
        line_axes[chart['line']] = "y2";
        if (chart['line-limits']) {
            axis_y2 = $.extend(axis_y2, {
                min: chart['line-limits'][0],
                max: chart['line-limits'][1],
                padding: 0,
            });
        }
    }

    let c3chart = c3.generate({
        bindto: `#${figure.attr('id')}`,
        size: {width: options.width, height: options.height},
        data: {
            type: 'bar',
            json: chart["data"],
            hide: hidden,
            color: colorfunc,  // used for color-by
            colors: options.colors,
            keys: {
                x: chart["x-label"],
                value: series
            },
            axes: chart["line"] && line_axes || {},
            types: chart["line"] && line_types || {},
            groups: chart["stack"] || [],
            order: null
        },
        grid: {y: {show: true}},
        axis: {
            x: {
                type: 'category',
                label: chart['x-label'],
                tick: x_ticks,
            },
            y: {
                tick: {format: formatKilo}
            },
            y2: axis_y2,
            rotated: (options.horizontal || false)
        },
        legend: {hide: (series.length === 1)},
        bar: {width: {ratio: .6}},
        padding: {bottom: 20},
        onresize: function () {
            this.api.resize({
                width: figure.width(),
                height: figure.width() * options.height / options.width
            });
        }
    });
    if (chart["annotations"]) {
        if (options.horizontal) {
            c3chart.ygrids(chart["annotations"])
        } else {
            c3chart.xgrids(chart["annotations"])
        }
    }
    figure.data('c3-chart', c3chart);
}


function drawHistogram(figure, chart, options) {
    migrateData(chart);
    let yscale = chart['y-scale'];
    let data = chart['data'];
    let x_culling = chart['x-culling'] || null;

    // remove raw data from dom
    figure.removeData('chart');
    figure.removeAttr('data-chart');

    let c3chart = c3.generate({
        bindto: `#${figure.attr('id')}`,
        size: {width: options.width, height: options.height},
        data: {
            type: 'bar',
            json: data,
            colors: {
                y: options.scheme[figure.parent().index()]
            },
            keys: {
                x: 'x', value: ['y']
            },
        },
        axis: {
            x: {
                tick: {
                    fit: false,
                    culling: {max: x_culling},
                    format: v => v.toFixed(1)
                }
            },
            y: {
                type: yscale
            }
        },
        legend: {hide: true},
        grid: {y: {show: true}},
        bar: {width: {ratio: 0.5}},
        onresize: function () {
            this.api.resize({
                width: figure.width(),
                height: figure.width() * options.height / options.width
            });
        }
    });
    figure.data('c3-chart', c3chart);
}

function drawPieChart(figure, chart, options) {
    let data = {};
    let series = [];
    let colors = {};

    // remove raw data from dom
    figure.removeData('chart');
    figure.removeAttr('data-chart');
    migrateData(chart);
    $.each(chart.data, function (i, item) {
        data[item.label] = item.value;
        series.push(item.label);
        colors[item.label] = item.color || options.scheme[i];
    });

    let c3chart = c3.generate({
        bindto: `#${figure.attr('id')}`,
        size: {width: options.width, height: options.height},
        data: {
            type: 'pie',
            json: [data],
            colors: colors,
            keys: {
                value: series
            },
        },
        onresize: function () {
            this.api.resize({
                width: figure.width(),
                height: figure.width() * options.height / options.width
            });
        }
    });
    figure.data('c3-chart', c3chart);
}


function drawScatterChart(figure, chart, options) {
    drawXYChart(figure, chart, options, 'scatter');
}

function drawLineChart(figure, chart, options) {
    drawXYChart(figure, chart, options, 'line');
}


function callout(g, value, color) {
    if (!value) return g.style("display", "none");

    if (g.attr('data-label')) {
        value = `${value} - ${g.attr('data-label')}`;
    }
    g.attr('data-label');

    g.style("display", null)
        .style("pointer-events", "none")
        .style("font", "10px sans-serif");

    const path = g.selectAll("path")
        .data([null])
        .join("path")
        .attr("fill", "var(--warning)")
        .attr("stroke", "black");

    const text = g.selectAll("text")
        .data([null])
        .join("text")
        .call(text => text
            .selectAll("tspan")
            .data((value + "").split(/\n/))
            .join("tspan")
            .attr("x", 0)
            .attr("y", (d, i) => `${i * 1.1}rem`)
            .style("font-weight", (_, i) => i ? null : "bold")
            .text(d => d));

    const {x, y, width: w, height: h} = text.node().getBBox();

    text.attr("transform", `translate(${-w / 2},${10 - y})`);
    path.attr("d", `M${-w / 2 - 10},5H-5l5,-5l5,5H${w / 2 + 10}v${h + 10}h-${w + 20}z`);
}


function drawTimeline(figure, chart, options) {

    let types = [];
    let margin = {top: 10, right: 10, bottom: 10, left: 10};
    let width = options.width - margin.left - margin.right;
    let height = 240;
    let xcenter = width / 2;

    // assign colors
    $.each(chart.data, function (i, entry) {
        if (!types.includes(entry.type)) {
            types.push(entry.type);
        }
    });
    types.sort();
    let color_scheme = ColorSchemes[chart.colors] || ColorSchemes.Tableau10;
    let colors = d3.scaleOrdinal().domain(types).range(color_scheme);
    let timeline = d3.timeline()
        .size([width, 150])
        .extent([chart.start, chart.end])
        .bandStart(d => d.start)
        .bandEnd(d => d.end)
        .padding(2);

    let timelineBands = timeline(chart.data);
    let x_scale = d3.scaleLinear()
        .domain([chart.start, chart.end])
        .range([0, width]);

    let x_axis = d3.axisBottom()
        .scale(x_scale)
        .tickFormat(d3.timeFormat('%H:%M'));

    let svg = d3.select(`#${figure.attr('id')}`)
        .append('svg')
        .attr('viewBox', `-${margin.left} -${margin.top} ${options.width} ${height}`)
        .attr('class', 'w-100');

    // add events
    svg.selectAll("rect.event")
        .data(timelineBands)
        .enter()
        .append("rect")
        .attr('class', 'event')
        .attr("x", function (d) {
            return d.start
        })
        .attr("x", function (d) {
            return d.start
        })
        .attr("y", function (d) {
            return d.y
        })
        .attr("height", function (d) {
            return d.dy
        })
        .attr("width", function (d) {
            return d.end - d.start
        })
        .attr("data-label", d => `${d.label}`)
        .attr("data-type", d => d.type)
        .attr('shape-rendering', 'geometricPrecision')
        .style("fill", d => colors(d.type))
        .style("stroke", d => colors(d.type))
        .attr('pointer-events', 'all')
        .on('mouseover', function () {
            tooltip.attr('data-label', $(this).data("label"));
        })
        .on('mouseout', function () {
            tooltip.attr('data-label', null);
        });

    // add x-axis
    svg.append("g")
        .call(x_axis)
        .attr("transform", "translate(0, 160)");

    // Add legend
    let size = 10;
    let left = 0;
    let offset = 80;
    let legend = svg.append("g");
    let legends = legend.selectAll(".legend")
        .data(types)
        .enter()
        .append("g")
        .attr('class', "legend")
        .attr('data-type', function (d, i) {
            return d
        })
        .attr('transform', function (d, i) {
            if (i === 0) {
                left = d.length + offset;
                return "translate(0,0)"
            } else {
                let curpos = left;
                left += d.length + offset;
                return `translate(${curpos}, 0)`;
            }
        })
        .on('mouseover', function () {
            let selector = $(this).data('type');
            svg.selectAll(`rect.event:not([data-type="${selector}"])`)
                .style('opacity', .1);
        })
        .on('mouseout', function () {
            svg.selectAll('rect')
                .style('opacity', 1);
        });

    legends.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', size)
        .attr('height', size)
        .style("fill", d => colors(d));
    legends.append('text')
        .attr('x', size + 10)
        .attr('y', size)
        .text(function (d, i) {
            return d
        })
        .style('text-anchor', 'start')
        .style('font-size', '10');

    // center legend in position
    let legendx = xcenter - left / 2;
    let legendy = height - margin.bottom - 30;
    legend.attr('transform', `translate(${legendx}, ${legendy})`);


    // mouse cursor and tooltip
    const tooltip = svg.append("g");
    const cursor = svg.append("g")
        .attr('class', 'mouse-cursor')
        .append("path")
        .attr('class', "mouse-line")
        .style('stroke', "var(--warning)")
        .style('stroke-width', '1px')
        .style('opacity', "0")
        .attr('pointer-events', 'none');

    svg
        .on('mouseleave', function () {
            d3.select('.mouse-line').style('opacity', 0);
            tooltip.call(callout, null);
        })
        .on('touchmove mousemove', function () {
            const mouse = d3.mouse(this);
            const info = d3.timeFormat('%H:%M %b %d, %Y')(x_scale.invert(mouse[0]));
            if (mouse[1] < 165) {
                d3.select('.mouse-line')
                    .style("opacity", 1)
                    .attr("d", function () {
                        return `M ${mouse[0]}, 160, ${mouse[0]} 0`;
                    });
                tooltip
                    .attr("transform", `translate(${mouse[0]}, 164)`)
                    .call(callout, info);
            } else {
                d3.select('.mouse-line').style('opacity', 0);
                tooltip.call(callout, null);
            }
        });

    // remove raw data from dom
    figure.removeData('chart').removeAttr('data-chart');

    // adjust font-size on resize
    window.onresize = function () {
        let scale = width / figure.width();
        svg.selectAll("text")
            .attr('transform', `scale(${scale} ${scale})`);
        svg.selectAll("line")
            .attr('stroke-width', `${scale}px`);
    }
}

function drawGeoChart(figure, chart, options) {
    google.charts.load('current', {
        'packages': ['geochart'],
    });
    google.charts.setOnLoadCallback(function () {
        let data = new google.visualization.DataTable();
        let table = [];

        if (chart.mode === 'markers') {
            data.addColumn('number', 'Latitude');
            data.addColumn('number', 'Longitude');
            data.addColumn('string', 'Name');
            data.addColumn('number', 'Value');
            $.each(chart.data, function (i, entry) {
                table.push([entry.Lat, entry.Lon, entry.Name, entry.Value]);
            });
        } else {
            data.addColumn('string', 'Location');
            data.addColumn('number', 'Value');
            $.each(chart.data, function (i, entry) {
                table.push([entry.Location, entry.Value]);
            });
        }
        data.addRows(table);
        let vis = new google.visualization.GeoChart(document.getElementById(`${figure.attr('id')}`));
        vis.draw(data, {
            region: chart.region,
            displayMode: chart['mode'] || 'auto',
            resolution: chart.resolution,
            colorAxis: {colors: options.scheme},
            backgroundColor: 'transparent',
            //defaultColor: 'transparent',
            legend: null,
            //sizeAxis: {minValue: 0, maxValue: 100},
            enableRegionInteractivity: true,
            //keepAspectRatio: true,
            height: options.height,
            width: options.width,
            tooltip: {isHtml: true}
        });
        google.visualization.events.addListener(vis, 'ready', function () {
            let svg = $(`#${figure.attr('id')} svg`);
            svg.attr('viewBox', `0 0 ${svg.attr("width")} ${svg.attr("height")}`);
            svg.removeAttr('width');
            svg.removeAttr('height');
            svg.parent().removeAttr('style').css('width', '100%');
            svg.parent().parent().removeAttr('style').css('width', '100%');
        });
    });
}


(function ($) {
    $.fn.showReport = function (options) {
        let target = $(this);
        let defaults = {
            data: {},
        };
        let settings = $.extend(defaults, options);

        target.addClass('report-viewer');
        $.each(settings.data.details, function (i, section) {
            target.append(sectionTemplate({id: i, section: section}))
        });

        target.find('figure').each(function () {
            let figure = $(this);
            let chart = decodeObj(figure.attr('data-chart'));
            let aspect_ratio = chart['aspect-ratio'] || 16 / 9;
            let chart_colors = chart.colors;
            if (typeof chart.data === 'object') {
                aspect_ratio = chart.data['aspect-ratio'] || aspect_ratio;
                chart_colors = chart.data.colors || chart_colors;
            }
            let options = {
                width: figure.width(),
                height: figure.width() / aspect_ratio,
                colors: {}
            };

            // if chart.data.colors is an array use it as a color scheme, if it is an
            // object, then assume it maps names to color values
            // if it is a string then assume it is a named color scheme in ColorSchemes

            if (Array.isArray(chart_colors)) {
                options.scheme = chart_colors;
            } else if (typeof chart_colors === 'object') {
                options.scheme = ColorSchemes.Tableau10;
                options.colors = chart_colors;
            } else {
                options.scheme = ColorSchemes[chart_colors] || ColorSchemes.Tableau10;
            }

            switch (figure.data('type')) {
                case 'barchart':
                    options.horizontal = true;
                    drawBarChart(figure, chart, options);
                    break;
                case 'columnchart':
                    drawBarChart(figure, chart, options);
                    break;
                case 'lineplot':
                    drawLineChart(figure, chart, options);
                    break;
                case 'histogram':
                    drawHistogram(figure, chart, options);
                    break;
                case 'pie':
                    drawPieChart(figure, chart, options);
                    break;
                case 'scatterplot':
                    drawScatterChart(figure, chart, options);
                    break;
                case 'timeline':
                    drawTimeline(figure, chart, options);
                    break;
                case 'geochart':
                    drawGeoChart(figure, chart, options);
                    break;
            }

            // caption
            if (chart.title) {
                figure.after(`<figcaption class="text-center">${chart.title}</figcaption>`);
            } else {
                figure.after(`<figcaption class="text-center"></figcaption>`);
            }

        });
    };
}(jQuery));