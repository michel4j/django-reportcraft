import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";
import _ from "https://cdn.jsdelivr.net/npm/underscore@1.13.7/+esm";
import showdown from "https://cdn.jsdelivr.net/npm/showdown@1.9.1/+esm";
import * as topojson from "https://cdn.jsdelivr.net/npm/topojson@3.0.2/+esm";
import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

export const figureTypes = [
    "bars",
    "columns",
    "xyplot",
    "pie",
    "donut",
    "histogram",
    "timeline",
    'geochart',

];

// Define custom color schemes
const ColorSchemes = {
    "Live4": ['#8f9f9a', '#c56052', '#9f6dbf', '#a0b552'],
    "Live8": ['#073b4c', '#06d6a0', '#ffd166', '#ef476f', '#118ab2', '#7f7eff', '#afc765', '#78c5e7'],
    "Live16": [
        '#67aec1', '#c45a81', '#cdc339', '#ae8e6b', '#6dc758', '#a084b6', '#667ccd', '#cd4f55',
        '#805cd6', '#cf622d', '#a69e4c', '#9b9795', '#6db586', '#c255b6', '#073b4c', '#ffd166'
    ],
};

const contentTemplate = _.template(
    '<div id="entry-<%= id %>" <% let style = entry.style || ""; %> class="section-entry <%= entry.kind %>-entry <%= style %>" >' +
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
    '       <% _.each(entry.data, function(table, t){ %>' +
    '       <%= tableTemplate({id: id, entry: entry, table: table, showCaption: (t == entry.data.length -1)}) %>' +
    '       <% }); %>' +
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
    '           <div class="section-title col-12"><h2><%= section.title %></h2></div>' +
    '       <% } %>' +
    '     <% _.each(section.content, function(entry, j){ %><%= renderContent({id: id+"-"+j, entry: entry}) %><% }); %>' +
    '</section>'
);

const tableTemplate = _.template(
    '<table id="table-<%= id %>" class="table table-sm table-hover">' +
    '<% if ((entry.title) && (showCaption))  { %>' +
    '   <caption class="text-center"><%= entry.title %></caption>' +
    '<% } %>' +
    '<% if (entry.header.includes("row")) { %>' +
    '   <thead><tr>' +
    '       <% _.each(table[0], function(cell, i){ %>' +
    '       <th><span><%= cell %></span></th>' +
    '       <% }); %>' +
    '   </tr></thead>' +
    '<% } %>' +
    '<tbody>' +
    '<% _.each(table, function(row, j){ %>' +
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


function renderMarkdown(text) {
    let markdown = new showdown.Converter();
    return markdown.makeHtml(text);
}


function renderContent(options) {
    return contentTemplate({
        id: options.id,
        entry: options.entry,
        renderMarkdown: renderMarkdown,
        tableTemplate: tableTemplate,
        figureTypes: figureTypes,
        encodeObj: encodeObj,
        decodeObj: decodeObj
    });
}


function renderSection(options) {
    return sectionTemplate({
        id: options.id,
        section: options.section,
        renderContent: renderContent,
        figureTypes: options.figureTypes,
        renderMarkdown: renderMarkdown,
    });
}


function encodeObj(obj) {
    // encode object as base64 string
    const utf8Bytes = encodeURIComponent(JSON.stringify(obj)).replace(/%([0-9A-F]{2})/g,
        function toSolidBytes(match, p1) {
            return String.fromCharCode(`0x${p1}`);
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


export function showReport(selector, sections, staticRoot = "/static/reportcraft/") {
    const target = document.querySelector(selector);

    if (!target) {
        console.error("Container Not found");
        return;
    }
    target.classList.add('report-viewer');          // add main class to the container

    // add sections to the container, we'll fill the content in a second pass
    sections.forEach(function(section, i) {
        const sectionHTML = renderSection({
            id: i,
            section: section,
        });
        target.insertAdjacentHTML('beforeend', sectionHTML);
    });
    
    // now fill the content with each section
    target.querySelectorAll('figure').forEach(function (figure, index) {
        const chart = decodeObj(figure.getAttribute('data-chart'));
        let aspectRatio = chart.data['aspect-ratio'] || 16/9;
        const options = {
            uid: (index + Date.now()).toString(36),
            // width: figure.offsetWidth,
            // height: figure.offsetWidth / aspectRatio,
            width: 800,
            height: 800 / aspectRatio,
            scheme: (ColorSchemes[chart.scheme] || d3[`scheme${chart.scheme}`]) || d3.Observable10,
            aspectRatio: aspectRatio,
            staticRoot: staticRoot,
        };

        switch (figure.dataset.type) {
            case 'bars':
            case 'columns':
                drawBarChart(figure, chart, options);
                break;
            case 'pie':
            case 'donut':
                drawPieChart(figure, chart, options);
                break;
            case 'xyplot':
                drawXYPlot(figure, chart, options);
                break;
            case 'histogram':
                drawHistogram(figure, chart, options);
                break;
            case 'timeline':
                drawTimeline(figure, chart, options);
                break;
            case 'geochart':
                drawGeoChart(figure, chart, options);
                break;
        }

        // Remove raw data from dom
        figure.removeAttribute('data-chart');

        // caption
        if (chart.title) {
            figure.insertAdjacentHTML('afterend', `<figcaption class="text-center">${chart.title}</figcaption>`);
        } else {
            figure.insertAdjacentHTML('afterend', `<figcaption class="text-center"></figcaption>`);
        }
    });
}

function formatTick(value, i, ticksEvery = 1, ticksInterval = undefined) {
    if (!(ticksInterval) && (i % ticksEvery)) {
        return null; // Skip this tick
    } else if (typeof(value) === 'string') {
        return value; // Return string as it is
    } else if (typeof(value) === 'number') {
        if (Number.isInteger(value)) {
            // Format integers with commas if they are larger than 10,000. This avoids
            // messing up years which are < 1e4
            return Math.abs(value) >= 1e4 ? value.toLocaleString() : value.toString();
        } else {
            return ""
        }
    }
}

function addFigurePlot(figure, plot) {
    // Fix the width and let CSS handle the height
    let svg = plot.querySelector('.rc-chart');
    if (plot.tagName === 'svg') {
        svg = plot;
    }
    if (svg) {
        svg.setAttribute('width', '100%');
        svg.removeAttribute('height'); // Let CSS handle the height
    }
    if (plot.tagName === "FIGURE") {
        // If the plot is a figure, we transfer its contents into the existing figure
        // Add last first to place legend at the bottom
        while (plot.lastChild) {
            figure.appendChild(plot.lastChild);
        }
    } else {
        // If the plot is not a figure, we add it to the figure
        figure.appendChild(plot);
    }
}

function setAxisScale(axisOptions, scale) {
    switch (scale){
        case 'linear':
            break;
        case 'time':
        case 'log':
        case 'symlog':
            axisOptions.type = scale;
            break;
        case 'log2':
            axisOptions.type = "log";
            axisOptions.base = 2;
            break;
        case 'inverse':
            axisOptions.transform = d => 1/d;
            break;
        case 'square':
            axisOptions.type = "pow";
            axisOptions.exponent = 2;
            break;
        case 'sqrt':
            axisOptions.type = "pow";
            axisOptions.exponent = 0.5;
            break;
        case 'cube':
            axisOptions.type = "pow";
            axisOptions.exponent = 3;
            break;
        case 'inv-square':
            axisOptions.type = "pow";
            axisOptions.exponent = -2;
            axisOptions.reverse = true;
            break;
        case 'inv-cube':
            axisOptions.type = "pow";
            axisOptions.exponent = -3;
            break;
        case 'cube-root':
            axisOptions.type = "pow";
            axisOptions.exponent = 1/3;
            break;
    }
}


function radiusLegend(data, options) {
    return new Plot.dot(data, {
        ...options,
        frameAnchor: "bottom-right",
        strokeWidth: 0.8,
        dx: -40,
        dy: -3,
        render: (i, s, v, d, c, next) => {
            const g = next(i, s, v, d, c);
            d3.select(g)
                .selectAll("circle")
                .each(function (i) {
                    const r = +this.getAttribute("r");
                    const x = +this.getAttribute("cx");
                    const y = +this.getAttribute("cy");
                    this.setAttribute("transform", `translate(0,${-r})`);
                    const title = d3.select(this).select("title");
                    d3.select(g)
                        .append("text")
                        .attr("x", x)
                        .attr("y", y - 2 * r - 4)
                        .attr("stroke", "none")
                        .attr("fill", "currentColor")
                        .text(title.text());
                    title.remove();
                });
            return g;
        }
    });
}

function drawBarChart(figure, chart, options) {
    let marks = [];
    const markTypes = chart.features || [];
    const valueAxis = (chart.kind === 'bars') ? 'x' : 'y';
    const categoryAxis = (chart.kind === 'bars') ? 'y' : 'x';
    const ticksEvery = chart["ticks-every"] || 1; // Default to every tick
    const ticksInterval = chart["ticks-interval"] || undefined; // Default to 1 for bar charts
    const fontSize = 10; //getFontSize();
    const colorScale = d3.scaleOrdinal(options.scheme);
    const valueScale = chart["scale"] || 'linear';
    let maxLabelLength = 10;

    const plotOptions = {
        className: "rc-chart",
        width: options.width || 800,
        color: {
            legend: true,
            range: options.scheme,
        },
        [categoryAxis]: {
            tickFormat: (d, i) => formatTick(d, i, ticksEvery, ticksInterval),
            interval: ticksInterval,
            label: null
        },
        [valueAxis]: {
            grid: true,
        },
        marks: marks
    };
    setAxisScale(plotOptions[valueAxis], valueScale);
    markTypes.forEach(function(mark, index){
        const markOptions = {x: mark.x,  y: mark.y, sort: null, tip: categoryAxis};

        maxLabelLength = Math.max(maxLabelLength, ...chart.data.map(d => `${d[mark[categoryAxis]]}`.length || 0));
        markOptions.fill = mark.colors || colorScale(index);
        if (mark.groups) {
            plotOptions[categoryAxis].axis = null;
            if (chart.kind === 'bars') {
                markOptions.fy = mark.groups;
            } else {
                markOptions.fx = mark.groups;
            }
        }
        if (mark.sort) {
            markOptions.sort = mark.sort.startsWith('-') ? {[categoryAxis]: `-${valueAxis}`}: {[categoryAxis]: valueAxis};
        }

        if (chart.kind === 'bars') {
            plotOptions.marginLeft = Math.max(40, maxLabelLength * fontSize * 0.8);
            marks.push(new Plot.ruleX([0]));
            marks.push(new Plot.barX(chart.data, markOptions));
        } else {    // columns
            plotOptions.height = options.height || 400;
            plotOptions.marginBottom = fontSize * 3;
            marks.push(new Plot.ruleY([0]));
            marks.push(new Plot.barY(chart.data, markOptions));
        }
    });

    // Create the bar chart
    const plot = Plot.plot(plotOptions);
    addFigurePlot(figure, plot);
}

function drawXYPlot(figure, chart, options) {
    let marks = [];
    const markTypes = chart.features || [];
    const colorScale = d3.scaleOrdinal(options.scheme);
    const xScale = chart["x-scale"] || 'linear';
    const yScale = chart["y-scale"] || 'linear';

    const plotOptions = {
        className: "rc-chart",
        width: options.width || 800,
        height: options.height || 600,
        marginLeft: 40,
        marginRight: 40,
        marginTop: 40,
        marginBottom: 40,
        color: {
            legend: true,
            range: options.scheme,
        },
        x: {
            grid: true,
            label: chart["x-label"] || undefined,
        },
        y: {
            grid: true,
            label: chart["y-label"] || undefined,
        },
        r: {
            transform: (r) => Math.pow(r, 2), // Square the radius so that area is proportional to value
        },
        marks: marks
    };

    // Set scales
    setAxisScale(plotOptions.x, xScale);
    setAxisScale(plotOptions.y, yScale);

    markTypes.forEach(function(mark, index){
        const markOptions = {
            x: mark.x,
            y: mark.y,
            r: mark.z || undefined,
            curve: mark.curve || "linear",
            tip: true,
        };
        if (mark.type === 'line') {
            markOptions.stroke = mark.colors || colorScale(index);
            marks.push(new Plot.lineY(chart.data, markOptions));
        } else if (mark.type === 'line-points') {
            markOptions.stroke = mark.colors || colorScale(index);
            markOptions.marker = mark.marker || 'circle-stroke';
            marks.push(new Plot.lineY(chart.data, markOptions));
        } else if (mark.type === 'points') {
            markOptions.stroke = mark.colors || colorScale(index);
            markOptions.strokeWidth = 1;
            marks.push(new Plot.dot(chart.data, markOptions));
        }else if (mark.type === 'points-filled') {
            markOptions.fill = mark.colors || colorScale(index);
            markOptions.stroke = "var(--bs-body-color)";
            markOptions.strokeWidth = 0.5;
        } else if (mark.type === 'area') {
            markOptions.fill = mark.colors || colorScale(index);
            marks.push(new Plot.areaY(chart.data, markOptions));
        } else {
            console.warn(`Unknown XY Plot: ${mark.type}`);
        }
        if (chart['cross-hair']) {
            marks.push(new Plot.crosshair(chart.data, {'x': mark.x, 'y': mark.y}));
        }
    });
    // Create chart
    const plot = Plot.plot(plotOptions);
    addFigurePlot(figure, plot);
}


function drawHistogram(figure, chart, options) {
    const binInput = {y: "count"};
    const binOutput = {x: {value: chart.values, thresholds: chart.bins || 'auto' }};
    const plotOptions = {
        className: "rc-chart",
        width: options.width || 800,
        height: options.height || 600,
        marginLeft: 40,
        marginRight: 40,
        marginTop: 40,
        marginBottom: 40,
        color: {
            range: options.scheme,
        },
        y: { grid: true},
        marks: []
    };
    if (chart["groups"]) {
        plotOptions.color.legend = true;
        binOutput.fill = chart["groups"];
        if (!(chart.stack)) {
            binOutput.nudge = 1; // Avoid bars overlapping
            binInput.y = undefined;
            binInput.y2 = "count";
            binOutput.mixBlendMode = "multiply";
        }
    }
    plotOptions.marks = [
        Plot.rectY(chart.data, Plot.binX(binInput, binOutput)),
        Plot.ruleY([0])
    ];

    // Create chart
    const plot = Plot.plot(plotOptions);
    addFigurePlot(figure, plot);
}


function drawPieChart(figure, chart, options) {
    // Placeholder for pie chart implementation
    const uniqueLabels = [...d3.union(chart.data.map(d => d.label))];
    const color = d3.scaleOrdinal(options.scheme);
    const outerRadius = Math.min(options.width, options.height) / 2 - 15;
    const innerRadius = (chart.kind === 'donut') ? outerRadius / 2 : 0;

    // Add chart
    const svg = d3.select(figure)
        .append("svg")
        .attr("viewBox", `0 0 ${options.width} ${options.height}`)
        .attr("class", "rc-chart")
        .attr("width", "100%")
        .append("g")
        .attr("transform", `translate(${options.width / 2}, ${options.height / 2})`);

    const pie = d3.pie()
        .value(d => d.value);
    let dataReady = pie(chart.data);
    let arcGenerator = d3.arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius);

    svg.selectAll("pieSlices")
        .data(dataReady)
        .enter()
        .append("path")
            .attr("d", arcGenerator)
            .attr("fill", d => color(d.data.label))
            .attr("stroke", "var(--bs-body-bg)")
            .style("stroke-width", "1px")
            .style("opacity", 1);

    // Add legend
    const legend = d3.select(figure)
        .append("div")
        .attr("class", `legend rc-chart-swatches`)
        .style("min-height", "33px")
        .style("display", "flex")
        .style("flex-direction", "row")
        .style("flex-wrap", "wrap")
        .style("align-items", "center")
        .style("justify-content", "center");

    legend.selectAll("legendItem")
        .data(uniqueLabels)
        .enter()
        .append("span")
            .attr("class", "legend-item")
            .style("display", "inline-flex")
            .style("align-items", "center")
            .style("font-size", "10px")
            .style("margin-right", "10px")
            .style("margin-bottom", "5px")
            .html(d => `<svg width="15" height="15" style="margin-right: 0.5em;" fill="${color(d)}">
                        <rect width="100%" height="100%"></rect>
                        </svg>${d}`);

}


function drawTimeline(figure, chart, options) {
    const colorScale = d3.scaleOrdinal(options.scheme);
    const plotOptions = {
        className: "rc-chart",
        width: options.width || 800,
        height: options.height || 600,
        marginLeft: 40,
        marginRight: 40,
        marginTop: 40,
        marginBottom: 40,
        color: {
            range: options.scheme,
        },
        x: {
            axis: "top",
            grid: true,
        },
        y: {
            axis: null,
            label: null,
        },
    };

    plotOptions.marks = [
        Plot.barX(chart.data, {
            x1: chart.start,
            x2: chart.end,
            y: chart.labels,
            fill: chart.colors || colorScale(0),
            sort: {y: "x1"}
        }),
        Plot.text(chart.data, {
            x: chart.start,
            y: chart.labels,
            text: chart.labels,
            textAnchor: "end",
            dx: -3,
        })
    ]
    if (chart.colors) {
        plotOptions.color.legend = true;
    }
    plotOptions.marginLeft = 100;
    // Create chart
    const plot = Plot.plot(plotOptions);
    addFigurePlot(figure, plot);
}


function drawGeoChart(figure, chart, options) {
    const colorScale = d3.scaleOrdinal(options.scheme);
    let colorLegend = false;
    const plotOptions = {
        className: "rc-chart",
        width: options.width || 800,
        height: options.height || 600,
        color: {
            type: "quantize",
            //scheme: "greens",
        },
        projection: {},
        marks: []
    };

    d3.json(`${options.staticRoot}/maps/${chart.map}.json`).then(function(geoData) {
        const land = topojson.feature(geoData, geoData.objects.land);
        const map = topojson.feature(geoData, geoData.objects["subunits"] || geoData.objects["countries"]);

        if (chart.map === '001') {  // World map, no need to show land
            plotOptions.projection = {
                type: "mercator",
                rotate: [-11.6, 0],
                domain: map,
            }
        } else {
            const centroid = d3.geoCentroid(map);
            plotOptions.projection = {
                type: "orthographic",
                rotate: [-centroid[0], -centroid[1]],
                domain: map,
                inset: 5
            }
            plotOptions.marks.push(Plot.geo(land, {fill: "var(--bs-secondary)", fillOpacity: 0.1}));
        }
        plotOptions.marks.push(
            Plot.geo(map, {stroke: "var(--bs-body-color)", strokeWidth: 1}),
            Plot.graticule({strokeOpacity: 0.05}),
        );

        // add features now

        chart.features.forEach(function(feature, index) {
            switch (feature.type) {
                case 'area':
                    let locMap = new Map(chart.data.map(d => [d[chart.location], d[feature.value]]))
                    plotOptions.marks.push(
                        Plot.geo(map, {
                            fill: d => locMap.get(d.id),
                            stroke: "var(--bs-body-color)",
                            strokeWidth: 0.5,
                        }),
                    )
                    colorLegend = true;
                    break;
                case 'bubble':
                    plotOptions.marks.push(
                        new Plot.dot(chart.data, {
                            x: chart.longitude,
                            y: chart.latitude,
                            r: feature.value,
                            strokeWidth: 0.5,
                            stroke: feature.value,
                            opacity: 0.7
                        })
                    );
                    break;
                case 'density':
                    plotOptions.marks.push(
                        new Plot.density(chart.data, {
                            x: chart.longitude,
                            y: chart.latitude,
                            weight: feature.value,
                            opacity: 0.7,
                        })
                    )
                    break;
                case 'markers':
                    plotOptions.marks.push(
                        new Plot.text(chart.data, {
                            x: chart.longitude,
                            y: chart.latitude,
                            text: feature.value,
                            fill: "black",
                            textAnchor: "middle",
                        })
                    )
                    break;
            }
        });

        switch (chart.labels) {
            case 'names':
            case 'codes':
                const isCode = (chart.labels === 'codes') || false;
                plotOptions.marks.push(
                    Plot.text(
                        map.features,
                        Plot.centroid({
                            text: (d) => isCode? d.id: d.properties.name,
                            textAnchor: "middle",
                            tip: true,
                            fill: "var(--bs-body-color)",
                            stroke: "white",
                            strokeWidth: 0.5,
                            paintOrder: "stroke",
                            fontSize: 8,
                            dy: 3
                        })
                    )
                );
                break;
            case 'places':
                if (geoData.objects.places) {
                    const places = topojson.feature(geoData, geoData.objects.places);
                    plotOptions.marks.push(
                        Plot.dot(places, {
                            filter: (d) => d.properties.scalerank < 5, // Show only major places
                            x: (d) => d.geometry.coordinates[0],
                            y: (d) => d.geometry.coordinates[1],
                            fill: "currentColor",
                            r: 1,
                        }),
                        Plot.text(places, {
                            filter: (d) => d.properties.scalerank < 5, // Show only major places
                            x: (d) => d.geometry.coordinates[0],
                            y: (d) => d.geometry.coordinates[1],
                            text: (d) => d.properties.name,
                            textAnchor: "middle",
                            tip: true,
                            fill: "var(--bs-body-color)",
                            stroke: "white",
                            strokeWidth: 0.5,
                            paintOrder: "stroke",
                            fontSize: 8,
                            marker: true,
                            dy: 3
                        })
                    );
                }
                break;
        }

        if (colorLegend) {
            plotOptions.color.legend = true;
        }

        // Create chart
        const plot = Plot.plot(plotOptions);
        addFigurePlot(figure, plot);
    });
}