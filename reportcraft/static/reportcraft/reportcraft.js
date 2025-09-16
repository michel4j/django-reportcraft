import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";
import _ from "https://cdn.jsdelivr.net/npm/underscore@1.13.7/+esm";
import showdown from "https://cdn.jsdelivr.net/npm/showdown@1.9.1/+esm";
import * as topojson from "https://cdn.jsdelivr.net/npm/topojson@3.0.2/+esm";
import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";
import {OutputType, Svg2Roughjs} from "https://cdn.jsdelivr.net/npm/svg2roughjs@3.2.1/+esm";

export const figureTypes = [
    "bars",
    "columns",
    "xyplot",
    "pie",
    "donut",
    "histogram",
    "timeline",
    'geochart',
    'likert',
];

// Define custom color schemes
const ColorSchemes = {
    "Live4": [
        '#073b4c', '#06d6a0', '#ffd166', '#ef476f',
    ],
    "Live8": [
        '#073b4c', '#06d6a0', '#ffd166', '#ef476f',
        '#287DFF', '#82AFB7', '#B28600', '#DADADA'
    ],
    "Live16": [
        '#67aec1', '#c45a81', '#cdc339', '#ae8e6b',
        '#6dc758', '#a084b6', '#667ccd', '#cd4f55',
        '#805cd6', '#cf622d', '#a69e4c', '#9b9795',
        '#6db586', '#c255b6', '#073b4c', '#ffd166'
    ],
    "CarbonDark": [
        '#8a3ffc', '#33b1ff', '#007d79', '#ff7eb6',
        '#fa4d56', '#fff1f1', '#6fdc8c', '#4589ff',
        '#d12771', '#d2a106', '#08bdba', '#bae6ff',
        '#ba4e00', '#d4bbff'
    ],
    "Carbon": [
        '#6929c4', '#1192e8', '#005d5d', '#9f1853',
        '#fa4d56', '#570408', '#198038', '#002d9c',
        '#ee538b', '#b28600', '#009d9a', '#012749',
        '#8a3800', '#a56eff'
    ]
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
    '       <figure id="figure-<%= entry.id || id %>" data-type="<%= entry.kind %>" ' +
    '           data-rc-theme="<%= theme || null %>" data-chart="<%= encodeObj(entry) %>" >' +
    '       </figure>' +
    '   <% }%>' +
    '   <% if (entry.notes) { %>' +
    '       <div class="notes"><%= renderMarkdown(entry.notes) %></div>' +
    '   <% } %>' +
    '</div>'
);
const sectionTemplate = _.template(
    '<section id="section-<%= id %>" <% let style = section.style || "row"; %>' +
    '     class="<%= style %>">' +
    '     <%  if (section.title)  {%>' +
    '         <div class="section-title col-12"><h2><%= section.title %></h2></div>' +
    '     <% } %>' +
    '     <% _.each(section.content, function(entry, j){ %>' +
    '         <%= renderContent({id: id+"-"+j, entry: entry, theme: section.theme }) %>' +
    '     <% }); %>' +
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
    '               <td class="table-cell-<%= typeof cell %>" ><%= cell %></td>' +
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
        theme: options.theme,
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

function Likert(responses) {
    const map = new Map(responses);
    return {
        order: Array.from(map.keys()),
        offset(I, X1, X2, Z) {
            for (const stacks of I) {
                for (const stack of stacks) {
                    const k = d3.sum(stack, (i) => (X2[i] - X1[i]) * (1 - map.get(Z[i]))) / 2;
                    for (const i of stack) {
                        X1[i] -= k;
                        X2[i] -= k;
                    }
                }
            }
        }
    };
}

export function showReport(selector, sections, staticRoot = "/static/reportcraft/") {
    const target = document.querySelector(selector);

    if (!target) {
        console.error("Container Not found");
        return;
    }
    target.classList.add('report-viewer');          // add main class to the container

    // add sections to the container, we'll fill the content in a second pass
    sections.forEach(function (section, i) {
        const sectionHTML = renderSection({
            id: i,
            section: section,
        });
        target.insertAdjacentHTML('beforeend', sectionHTML);
    });

    // now fill the content with each section
    target.querySelectorAll('figure').forEach(function (figure, index) {
        const chart = decodeObj(figure.getAttribute('data-chart'));
        let aspectRatio = chart.data['aspect-ratio'] || 16 / 9;
        let scheme;

        if (chart.scheme in ColorSchemes) {
            scheme = ColorSchemes[chart.scheme];
        } else if (`scheme${chart.scheme}` in d3) {
            scheme = chart.scheme;
        } else if (`interpolate${chart.scheme}` in d3) {
            scheme = d3[`interpolate${chart.scheme}`];
        } else {
            scheme = d3.Observable10;
        }
        const targetWidth = figure.offsetWidth;
        const options = {
            uid: (index + Date.now()).toString(36),
            width: targetWidth,
            fontSize: scaleFontSize(targetWidth, 0.75, 2, 400, 1200),
            height: targetWidth / aspectRatio,
            scheme: scheme,
            theme: figure.getAttribute('data-rc-theme') || 'default',
            aspectRatio: aspectRatio,
            staticRoot: staticRoot,
        };

        // set theme for the figure
        figure.style.fontSize = '0.95rem'; // Set a base font size for the figure
        if (figure.getAttribute('data-rc-theme') === 'sketch') {
            figure.style.fontFamily = 'var(--rc-script-font)';
        } else {
            figure.style.fontFamily = 'var(--bs-font-sans-serif)'
        }

        try {
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
                case 'likert':
                    drawLikertChart(figure, chart, options);
                    break;
            }
        } catch (error) {
            //figure.innerHTML = `<div class="alert alert-warning py-5" role="alert"><pre>${error.stack}</pre></div>`;
            console.error("Error rendering chart:", error);
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
    if (i % ticksEvery) {
        return null; // Skip this tick
    } else if (typeof (value) === 'string') {
        return value; // Return string as it is
    } else if (typeof (value) === 'number') {
        if (Number.isInteger(value)) {
            // Format integers with commas if they are larger than 10,000. This avoids
            // messing up years which are < 1e4
            return Math.abs(value) >= 1e4 ? value.toLocaleString() : value.toString();
        } else {
            return ""
        }
    }
}

function setColorScheme(plotOptions, chartOptions) {
    switch (typeof chartOptions.scheme) {
        case 'string':
            plotOptions.color.scheme = chartOptions.scheme;
            break;
        case 'function':
            plotOptions.color.interpolate = chartOptions.scheme;
            plotOptions.color.type = 'quantize';
            break;
        case 'object':
            if (Array.isArray(chartOptions.scheme)) {
                plotOptions.color.range = chartOptions.scheme;
            }
            break;
        default:
            console.warn("Unknown color scheme format");
    }
}

function getFontSize(element) {
    if (!element || !(element instanceof Element)) {
        console.error("Invalid input: Please provide a valid DOM element.");
        return 12; // Default font size
    }

    const computedStyle = window.getComputedStyle(element);
    const fontSizeString = computedStyle.getPropertyValue('font-size');
    return parseFloat(fontSizeString);
}

function getCanvasFont(element = document.body) {
    // Get the font properties of the element
    const style = window.getComputedStyle(element);
    const fontSize = style.getPropertyValue('font-size') || "16px";
    const fontFamily = (style.getPropertyValue('font-family') || 'Fira Sans').replace(/["']/g, '');
    return `${fontSize} ${fontFamily}`;
}

/**
 * A function to calculate the rendered width of text in a given element.
 *
 * It uses a single, shared canvas element and caches the measured widths of
 * individual characters for each specific font style. This avoids costly DOM
 * manipulations and repeated measurements.
 *
 * @returns {function(string, HTMLElement): number} A function that takes text
 * and an element and returns the text's width in pixels.
 */
const getTextWidth = (() => {
    // Create a single canvas element to be reused for all measurements.
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    const fontCache = {};

    /**
     * Measures the width of a text string given a specific element's styling.
     * @param {string} text The text to measure.
     * @param {HTMLElement} element The element that defines the font styles.
     * @returns {number} The width of the text in pixels.
     */
    return function (text, element) {
        if (!text || !element) {
            return 0;
        }

        // Get the complete font string from the element's computed styles.
        const font = getCanvasFont(element);
        if (!fontCache[font]) {
            fontCache[font] = {};
        }

        // Set the canvas context's font to match the element's font.
        context.font = font;
        const charCache = fontCache[font];
        let width = 0;

        // Iterate over each character in the text.
        for (let i = 0; i < text.length; i++) {
            const char = text[i];
            // Check if the width of this character is already cached.
            let charWidth = charCache[char];
            if (charWidth === undefined) {
                // If not, measure it, store it in the cache, and then use it.
                charWidth = context.measureText(char).width;
                charCache[char] = charWidth;
            }
            width += charWidth;
        }
        return Math.round(width);
    };
})();

function scaleFontSize(width, minFontSize, maxFontSize, minWidth, maxWidth) {
    const clampedWidth = Math.max(minWidth, Math.min(maxWidth, width));
    const widthRange = maxWidth - minWidth;
    const fontSizeRange = maxFontSize - minFontSize;

    let scaledFontSize;

    if (widthRange === 0) { // Handle cases where minDivWidth and maxDivWidth are the same
        scaledFontSize = minFontSize;
    } else {
        const scaleFactor = (clampedWidth - minWidth) / widthRange;
        scaledFontSize = minFontSize + (fontSizeRange * scaleFactor);
    }
    return scaledFontSize;
}

function roughenSVG(svg, scalable = false) {
    const container = document.createElement('div');
    const svgConverter = new Svg2Roughjs(container, OutputType.SVG);
    svgConverter.svg = svg;
    svgConverter.roughConfig = {
        roughness: 1.5,
        bowing: 1.1,
        fillStyle: 'zigzag',
    };
    svgConverter.fontFamily = 'var(--rc-script-font)';
    svgConverter.sketch();

    // transfer svg attributes
    const newSvg = container.querySelector('svg');
    for (const attr of svg.attributes) {
        newSvg.setAttribute(attr.name, attr.value);
    }
    if (scalable) {
        newSvg.removeAttribute('height'); // Let CSS handle the height
        newSvg.setAttribute('width', '100%');
    }
    svg.replaceWith(newSvg);
}

function addFigurePlot(figure, plot) {

    let svg = plot.querySelector('.rc-chart');
    if (plot.tagName === 'svg') {
        svg = plot;
    }

    // remove styles added ty Plot.swatches
    let swatchStyle = plot.querySelector('.rc-chart-swatches > style');
    if (swatchStyle) {
        swatchStyle.remove();
    }

    // Fix the width and let CSS handle the height
    if (svg) {
        svg.setAttribute('width', '100%');
        svg.removeAttribute('height'); // Let CSS handle the height
        svg.removeAttribute('font-size'); // Let CSS handle the font size
        svg.removeAttribute('font-family'); // Let CSS handle the font family
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

    if (figure.getAttribute('data-rc-theme') === 'sketch') {
        figure.querySelectorAll('svg').forEach(function (svg) {
            // roughen the svg
            roughenSVG(svg, svg.classList.contains('rc-chart'));
        });

    }
}

function setAxisScale(axisOptions, scale) {
    switch (scale) {
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
            axisOptions.transform = d => 1 / d;
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
            axisOptions.exponent = 1 / 3;
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
    const valueAxis = (chart.kind === 'bars') ? 'x' : 'y';
    const categoryAxis = (chart.kind === 'bars') ? 'y' : 'x';
    const ticksEvery = chart["ticks-every"] || 1; // Default to every tick
    const ticksInterval = chart["ticks-interval"] || undefined; // Default to 1 for bar charts
    const colorScale = d3.scaleOrdinal(options.scheme);
    const valueScale = chart["scale"] || 'linear';
    const markOptions = {x: chart.x, y: chart.y, sort: null, tip: categoryAxis};
    const fontSizePix = getFontSize(figure);

    let maxLabelLength = 1;

    const plotOptions = {
        className: "rc-chart",
        style: {
            fontSize: '1em',
        },
        width: options.width,
        color: {
            legend: true,
        },
        [categoryAxis]: {
            tickFormat: (d, i) => formatTick(d, i, ticksEvery, ticksInterval),
            type: 'band',
            interval: ticksInterval,
            label: null,
            nice: true,
        },
        [valueAxis]: {
            grid: true,
        },
        marks: marks
    };
    setColorScheme(plotOptions, options);
    setAxisScale(plotOptions[valueAxis], valueScale);

    maxLabelLength = Math.max(maxLabelLength, ...chart.data.map(d => getTextWidth(`${d[chart.y]}`, figure)));
    markOptions.fill = chart.colors || colorScale(0);

    if (chart.grouped) {
        plotOptions[categoryAxis].axis = null;
        plotOptions[categoryAxis].interval = null;
        markOptions[`f${categoryAxis}`] = chart[categoryAxis];
        markOptions[categoryAxis] = chart.colors;
        plotOptions[`f${categoryAxis}`] = {
            tickFormat: (d, i) => formatTick(d, i, ticksEvery, ticksInterval),
            type: 'band',
            interval: ticksInterval,
            label: null,
        }
    } else if (chart.normalize) {
        markOptions.offset = "normalize";
        plotOptions[valueAxis].tickFormat = '%';
    }
    if (chart.facets) {
        markOptions[`f${valueAxis}`] = chart.facets;
        if (valueAxis === 'x') {
            plotOptions.marginTop = fontSizePix * 3;
        }
    }

    if (chart.sort) {
        markOptions.sort = chart.sort.startsWith('-') ? {[categoryAxis]: `-${valueAxis}`} : {[categoryAxis]: valueAxis};
    }

    plotOptions.marginLeft = Math.max(fontSizePix * 3, maxLabelLength);
    if (chart.kind === 'bars') {
        marks.push(new Plot.ruleX([0]));
        marks.push(new Plot.barX(chart.data, markOptions));
    } else {    // columns
        plotOptions.height = options.height || 400;
        plotOptions.marginBottom = fontSizePix * 3;
        marks.push(new Plot.ruleY([0]));
        marks.push(
            new Plot.barY(
                chart.data,
                markOptions
            ),
        );
    }

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
    let maxLabelLength = 1;
    const colorDomain = [];
    const colorRange = [];

    const plotOptions = {
        className: "rc-chart",
        width: options.width || 800,
        height: options.height || 600,
        marginLeft: 40,
        marginRight: 40,
        marginTop: 40,
        marginBottom: 40,
        style: {
            fontSize: '1em',
        },
        color: {
            legend: true,
        },
        x: {
            grid: true,
            label: chart["x-label"] || undefined,
            tickFormat: (d, i) => formatTick(d, i),
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
    setColorScheme(plotOptions, options);
    setAxisScale(plotOptions.x, xScale);
    setAxisScale(plotOptions.y, yScale);


    markTypes.forEach(function (mark, index) {
        maxLabelLength = Math.max(maxLabelLength, ...chart.data.map(d => `${d[mark.y]}`.length || 0));
        const markOptions = {
            x: mark.x,
            y: mark.y,
            r: mark.z || undefined,
            curve: mark.curve || "linear",
            tip: true,
        };
        let colorValue;
        if (mark.colors) {
            colorValue = mark.colors;
        } else {
            colorValue = colorScale(index);
            colorDomain.push(mark.y);
            colorRange.push(colorValue);
        }
        if (mark.type === 'line') {
            markOptions.stroke = colorValue;
            marks.push(new Plot.lineY(chart.data, markOptions));
        } else if (mark.type === 'line-points') {
            markOptions.stroke = colorValue;
            markOptions.marker = mark.marker || 'circle-stroke';
            marks.push(new Plot.lineY(chart.data, markOptions));
        } else if (mark.type === 'points') {
            markOptions.stroke = colorValue;
            markOptions.strokeWidth = 1;
            marks.push(new Plot.dot(chart.data, markOptions));
        } else if (mark.type === 'points-filled') {
            markOptions.fill = colorValue;
            markOptions.stroke = "var(--bs-body-color)";
            markOptions.strokeWidth = 0.5;
        } else if (mark.type === 'area') {
            markOptions.fill = colorValue;
            marks.push(new Plot.areaY(chart.data, markOptions));
        } else {
            console.warn(`Unknown XY Plot: ${mark.type}`);
        }
        if (chart['cross-hair']) {
            marks.push(new Plot.crosshair(chart.data, {'x': mark.x, 'y': mark.y}));
        }
    });
    // Create chart
    plotOptions.marginLeft = Math.max(20, maxLabelLength * getFontSize(figure));
    if (colorDomain.length > 1) {
        plotOptions.color = {
            domain: colorDomain,
            range: colorRange,
            legend: true,
        }
    }
    const plot = Plot.plot(plotOptions);
    addFigurePlot(figure, plot);
}


function drawHistogram(figure, chart, options) {
    const binInput = {y: "count"};
    const binOutput = {x: {value: chart.values, thresholds: chart.bins || 'auto'}};
    const plotOptions = {
        className: "rc-chart",
        style: {
            fontSize: '1em',
        },
        width: options.width || 800,
        height: options.height || 600,
        marginLeft: 40,
        marginRight: 40,
        marginTop: 40,
        marginBottom: 40,
        color: {
            range: options.scheme,
        },
        y: {grid: true},
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
    const total = d3.sum(chart.data, d => d.value);

    // Add plot
    const plot = document.createElement("figure");

    // Add legend
    const legend = d3.select(plot)
        .append("div")
        .attr("class", `legend rc-chart-swatches rc-swatches-wrap`)
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
        .attr("class", "rc-chart-swatch")
        .style("display", "inline-flex")
        .style("align-items", "center")
        .style("font-size", '1em')
        .style("margin-right", "10px")
        .style("margin-bottom", "5px")
        .html(d => `<svg width="15" height="15" fill="${color(d)}">
                        <rect width="100%" height="100%"></rect>
                        </svg>${d}`);

    // Add svg
    const svg = d3.select(plot)
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
        .style("opacity", 1)
        .append("text")
        .attr("class", "pie-label")
        .attr("transform", function (d) {
            const centroid = arcGenerator.centroid(d);
            return `translate(${centroid[0]}, ${centroid[1]})`;
        })
        .attr("text-anchor", "middle")
        .attr("stroke", "var(--bs-body-color)")
        .text(function (d) {
            console.log('calculating percentage', d);
            const percent = (100 * d.value / total);
            return d3.format(".1f")(percent) + "%";
        });

    addFigurePlot(figure, plot);
}


function drawTimeline(figure, chart, options) {
    const colorScale = d3.scaleOrdinal(options.scheme);
    const plotOptions = {
        className: "rc-chart",
        style: {
            fontSize: '1em',
        },
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
            tickFormat: (d, i) => formatTick(d, i),
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
    let colorLegend = false;
    let showLand = chart.map === '001' ? false : (chart["show-land"] || true);
    const plotOptions = {
        className: "rc-chart",
        style: {
            fontSize: '1em',
        },
        width: options.width || 800,
        height: options.height || 600,
        color: {
            type: "quantize",
        },
        projection: {},
        marks: []
    };

    setColorScheme(plotOptions, options);
    Promise.all([
        d3.json(`${options.staticRoot}/maps/${chart.map}.json`),
        showLand ? d3.json(`${options.staticRoot}/maps/land.json`) : null,
    ]).then(function ([geoData, landData]) {
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
        }

        // show land if needed
        if (showLand && landData) {
            const land = topojson.feature(landData, landData.objects.land);
            plotOptions.marks.push(Plot.geo(land, {fill: "var(--bs-secondary)", fillOpacity: 0.1}));
        }
        plotOptions.marks.push(
            Plot.geo(map, {stroke: "var(--bs-body-color)", strokeWidth: 1}),
            //Plot.graticule({strokeOpacity: 0.05}),
        );

        // add features now
        chart.features.forEach(function (feature, index) {
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
                            text: (d) => isCode ? d.id : d.properties.name,
                            textAnchor: "middle",
                            tip: true,
                            fill: "var(--bs-body-color)",
                            stroke: options.theme === 'default' ? "var(--bs-body-bg)" : null,
                            strokeOpacity: 0.7,
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
                            strokeOpacity: 0.7,
                            paintOrder: "stroke",
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

function drawLikertChart(figure, chart, options) {
    let maxLabelLength = 1;
    maxLabelLength = Math.max(maxLabelLength, ...chart.data.map(d => getTextWidth(`${d[chart.questions]}`, figure)));
    const likert = Likert(chart.domain.map(d => [d[0], Math.sign(d[1])]));
    const plotOptions = {
        className: "rc-chart",
        style: {
            fontSize: '1em',
        },
        width: options.width,
        color: {
            legend: true,
            scheme: options.scheme,
            domain: likert.order,
        },
        x: {
            tickFormat: Math.abs
        },
        marks: [
            Plot.barX(
                chart.data,
                Plot.stackX({
                    x: chart.counts,
                    y: chart.questions,
                    sort: chart.scores,
                    fill: chart.answers,
                    ...likert
                })
            ),
            Plot.ruleX([0])
        ]
    };

    // Create the bar chart
    plotOptions.marginLeft = Math.max(30, maxLabelLength);
    const plot = Plot.plot(plotOptions);
    addFigurePlot(figure, plot);
}