// Smart Beta Portfolio Dashboard
// Handles both Individual Indices and Portfolio Strategy tabs

// ==========================================
// TAB SWITCHING
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    // Tab switching logic
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;

            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');

            // Resize Plotly charts when switching tabs (charts rendered in hidden tabs have incorrect dimensions)
            if (targetTab === 'portfolio') {
                setTimeout(() => {
                    const chartIds = ['chart-nav', 'chart-sip-value', 'chart-drawdown',
                        'chart-rolling', 'chart-attribution', 'chart-alpha'];
                    chartIds.forEach(id => {
                        const elem = document.getElementById(id);
                        if (elem && elem.layout) {
                            Plotly.Plots.resize(elem);
                        }
                    });
                }, 100);
            }

            if (targetTab === 'nifty500-portfolio') {
                setTimeout(() => {
                    const chartIds = ['nifty500-chart-nav', 'nifty500-chart-sip-value', 'nifty500-chart-drawdown',
                        'nifty500-chart-rolling', 'nifty500-chart-attribution', 'nifty500-chart-alpha'];
                    chartIds.forEach(id => {
                        const elem = document.getElementById(id);
                        if (elem && elem.layout) {
                            Plotly.Plots.resize(elem);
                        }
                    });
                }, 100);
            }

            if (targetTab === 'nifty500-indices') {
                setTimeout(() => {
                    const chartIds = ['nifty500-momentum-chart', 'nifty500-value-chart', 'nifty500-ratio-chart'];
                    chartIds.forEach(id => {
                        const elem = document.getElementById(id);
                        if (elem && elem.layout) {
                            Plotly.Plots.resize(elem);
                        }
                    });
                }, 100);
            }

            if (targetTab === 'returns-analysis') {
                setTimeout(() => {
                    const chartIds = [
                        'ra-mom-10y', 'ra-mom-5y', 'ra-mom-3y', 'ra-mom-1y',
                        'ra-val-10y', 'ra-val-5y', 'ra-val-3y', 'ra-val-1y'
                    ];
                    chartIds.forEach(id => {
                        const elem = document.getElementById(id);
                        if (elem && elem.layout) {
                            Plotly.Plots.resize(elem);
                        }
                    });
                }, 100);
            }

            if (targetTab === 'nifty500-returns') {
                setTimeout(() => {
                    const chartIds = [
                        'ra-n500-mom-10y', 'ra-n500-mom-5y', 'ra-n500-mom-3y', 'ra-n500-mom-1y',
                        'ra-n500-val-10y', 'ra-n500-val-5y', 'ra-n500-val-3y', 'ra-n500-val-1y'
                    ];
                    chartIds.forEach(id => {
                        const elem = document.getElementById(id);
                        if (elem && elem.layout) {
                            Plotly.Plots.resize(elem);
                        }
                    });
                }, 100);
            }
        });
    });

    // Load all tabs' data
    loadIndicesData();
    loadPortfolioData();
    loadNifty500IndicesData();
    loadNifty500PortfolioData();
    loadReturnsAnalysis();
    loadNifty500ReturnsAnalysis();
});

// ==========================================
// INDIVIDUAL INDICES TAB
// ==========================================

async function loadIndicesData() {
    try {
        const response = await fetch('../nifty200/output/monthly/nifty200_dashboard_data.json');
        const data = await response.json();


        // Render individual index cards
        renderIndices(data.indices);

        // Load and render charts
        loadIndividualIndexCharts();  // New: Load Momentum and Value charts with MAs
        loadRatioChart();

        // Update insights
        updateInsights(data.indices);

    } catch (error) {
        console.error('Error loading indices data:', error);
    }
}

function renderIndices(indices) {
    const container = document.getElementById('indices-container');
    container.innerHTML = '';

    indices.forEach(index => {
        const card = createIndexCard(index);
        container.appendChild(card);
    });
}

function createIndexCard(index) {
    const card = document.createElement('div');
    card.className = 'index-card';

    const gainClass = index.absolute_gain >= 0 ? 'positive' : 'negative';

    card.innerHTML = `
        <div class="index-header">
            <h3 class="index-name">${index.name}</h3>
        </div>
        <div class="index-metrics">
            <div class="metric-row">
                <span class="metric-label">SIP XIRR</span>
                <span class="metric-value highlight">${index.sip_xirr.toFixed(2)}%</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Index CAGR</span>
                <span class="metric-value">${index.index_cagr.toFixed(2)}%</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Total Return</span>
                <span class="metric-value">${index.total_return.toFixed(2)}%</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Invested</span>
                <span class="metric-value">₹${formatNumber(index.total_invested)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Current Value</span>
                <span class="metric-value">₹${formatNumber(index.final_value)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Absolute Gain</span>
                <span class="metric-value ${gainClass}">₹${formatNumber(index.absolute_gain)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Max Drawdown</span>
                <span class="metric-value">${index.max_drawdown.toFixed(2)}%</span>
            </div>
            <div class="metric-row warning">
                <span class="metric-label">⭐ Max Investor DD</span>
                <span class="metric-value">${index.max_investor_drawdown.toFixed(2)}%</span>
            </div>
        </div>
    `;

    return card;
}

async function loadRatioChart() {
    try {
        const response = await fetch('../nifty200/output/weekly/ratio_chart.json');
        const chartData = await response.json();

        const chartDiv = document.getElementById('ratio-chart');
        Plotly.newPlot(chartDiv, chartData.data, chartData.layout, { responsive: true });
    } catch (error) {
        console.error('Error loading ratio chart:', error);
        document.getElementById('ratio-chart').innerHTML = '<p style="color: #ef4444; padding: 2rem;">Error loading chart</p>';
    }
}

async function loadIndividualIndexCharts() {
    try {
        const response = await fetch('../nifty200/output/nifty200_dashboard_data.json');
        const data = await response.json();

        if (!data.weekly_charts) {
            console.error('Weekly chart data not available');
            return;
        }

        const weeklyData = data.weekly_charts;

        // Render Momentum 30 Chart
        renderIndexChart(
            'momentum-chart',
            weeklyData.momentum.dates,
            weeklyData.momentum.close,
            weeklyData.momentum.ma_30,
            'Momentum 30 Index',
            '#8b5cf6'  // Purple
        );

        // Render Value 30 Chart
        renderIndexChart(
            'value-chart',
            weeklyData.value.dates,
            weeklyData.value.close,
            weeklyData.value.ma_30,
            'Value 30 Index',
            '#10b981'  // Green
        );

    } catch (error) {
        console.error('Error loading individual index charts:', error);
    }
}

function renderIndexChart(containerId, dates, closeValues, maValues, indexName, color) {
    const indexTrace = {
        x: dates,
        y: closeValues,
        type: 'scatter',
        mode: 'lines',
        name: indexName,
        line: { color: color, width: 2 },
        hovertemplate: '<b>Date:</b> %{x}<br>' +
            '<b>Close:</b> %{y:.2f}<br>' +
            '<extra></extra>'
    };

    const maTrace = {
        x: dates,
        y: maValues,
        type: 'scatter',
        mode: 'lines',
        name: '30-Week MA',
        line: { color: '#f59e0b', width: 1, dash: 'solid' },
        hovertemplate: '<b>Date:</b> %{x}<br>' +
            '<b>30W MA:</b> %{y:.2f}<br>' +
            '<extra></extra>'
    };

    const layout = {
        autosize: true,
        xaxis: {
            title: 'Date',
            showgrid: true,
            gridcolor: '#1e293b',
            color: '#94a3b8',
            zeroline: false
        },
        yaxis: {
            title: 'Index Value',
            showgrid: true,
            gridcolor: '#1e293b',
            color: '#94a3b8',
            zeroline: false,
            tickformat: ',.0f'
        },
        plot_bgcolor: '#0f172a',
        paper_bgcolor: '#0f172a',
        font: { family: 'Inter, sans-serif', color: '#f1f5f9' },
        hovermode: 'x unified',
        hoverlabel: {
            bgcolor: '#334155',
            font_size: 14,
            font_family: 'Inter'
        },
        margin: { l: 60, r: 40, t: 20, b: 60 },
        showlegend: true,
        legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.05, yanchor: 'bottom' }
    };

    const config = { responsive: true, displayModeBar: true };

    Plotly.newPlot(containerId, [indexTrace, maTrace], layout, config);
}

function updateInsights(indices) {
    // Find best performer by XIRR
    const bestPerformer = indices.reduce((best, current) =>
        current.sip_xirr > best.sip_xirr ? current : best
    );

    // Find lowest drawdown
    const lowestDD = indices.reduce((best, current) =>
        current.max_investor_drawdown > best.max_investor_drawdown ? current : best
    );

    document.getElementById('best-performer').textContent =
        `${bestPerformer.name} with ${bestPerformer.sip_xirr.toFixed(2)}% XIRR`;

    document.getElementById('lowest-dd').textContent =
        `${lowestDD.name} with ${lowestDD.max_investor_drawdown.toFixed(2)}% max investor drawdown`;
}

// ==========================================
// PORTFOLIO STRATEGY TAB
// ==========================================

async function loadPortfolioData() {
    try {
        const response = await fetch('../nifty200/output/nifty200_portfolio_dashboard.json');
        const data = await response.json();

        // Update KPI cards
        updateKPIs(data.kpis);

        // Render charts
        renderPortfolioCharts(data.charts);

        // Render calendar returns
        renderCalendarReturns(data.calendar_returns);

        // Render portfolio holdings log
        if (data.portfolio_holdings) {
            renderPortfolioHoldings(data.portfolio_holdings, 'portfolio-holdings-table');
        }

    } catch (error) {
        console.error('Error loading portfolio data:', error);
        document.querySelectorAll('.kpi-value').forEach(el => {
            el.textContent = 'Error';
        });
    }
}

function updateKPIs(kpis) {
    document.getElementById('kpi-xirr').textContent = `${kpis.sip_xirr}%`;
    document.getElementById('kpi-cagr').textContent = `${kpis.cagr}%`;
    document.getElementById('kpi-investor-dd').textContent = `${kpis.max_investor_dd}%`;
    document.getElementById('kpi-max-dd').textContent = `${kpis.max_drawdown}%`;
    document.getElementById('kpi-mar').textContent = kpis.mar_ratio.toFixed(2);
    document.getElementById('kpi-vol').textContent = `${kpis.volatility.toFixed(1)}%`;
    document.getElementById('kpi-total-return').textContent = `${kpis.total_return_pct}%`;
    document.getElementById('kpi-time-momentum').textContent = `${kpis.pct_time_momentum}%`;
}

function renderPortfolioCharts(charts) {
    // Chart 1: Portfolio NAV
    const navTrace = {
        x: charts.nav_series.dates,
        y: charts.nav_series.nav,
        type: 'scatter',
        mode: 'lines',
        name: 'Portfolio NAV',
        line: { color: '#8b5cf6', width: 2 }
    };

    const navLayout = {
        autosize: true,
        paper_bgcolor: '#1e293b',
        plot_bgcolor: '#1e293b',
        font: { color: '#f1f5f9', family: 'Inter' },
        yaxis: { type: 'log', gridcolor: '#334155' },
        xaxis: { gridcolor: '#334155' },
        margin: { l: 60, r: 40, t: 40, b: 60 }
    };

    const config = { responsive: true, displayModeBar: true };

    Plotly.newPlot('chart-nav', [navTrace], navLayout, config);

    // Chart 2: SIP Portfolio Value
    const sipInvestedTrace = {
        x: charts.sip_value_series.dates,
        y: charts.sip_value_series.invested,
        type: 'scatter',
        mode: 'lines',
        name: 'Total Invested',
        line: { color: '#94a3b8', width: 2, dash: 'dash' }
    };

    const sipValueTrace = {
        x: charts.sip_value_series.dates,
        y: charts.sip_value_series.value,
        type: 'scatter',
        mode: 'lines',
        name: 'Portfolio Value',
        fill: 'tonexty',
        line: { color: '#10b981', width: 2 }
    };

    Plotly.newPlot('chart-sip-value', [sipInvestedTrace, sipValueTrace], navLayout, config);

    // Chart 3: Underwater Drawdown Chart (Strategy + Individual Indices)
    const strategyDDTrace = {
        x: charts.drawdown_series.dates,
        y: charts.drawdown_series.strategy_dd,
        type: 'scatter',
        mode: 'lines',
        name: 'Strategy (Ratio Trend 75/25)',
        line: { color: '#8b5cf6', width: 3 },
        fill: 'tozeroy',
        fillcolor: 'rgba(139, 92, 246, 0.1)'
    };

    const momentumDDTrace = {
        x: charts.drawdown_series.dates,
        y: charts.drawdown_series.momentum_dd,
        type: 'scatter',
        mode: 'lines',
        name: 'Momentum 30 Index',
        line: { color: '#3b82f6', width: 2, dash: 'dot' }
    };

    const valueDDTrace = {
        x: charts.drawdown_series.dates,
        y: charts.drawdown_series.value_dd,
        type: 'scatter',
        mode: 'lines',
        name: 'Value 30 Index',
        line: { color: '#10b981', width: 2, dash: 'dot' }
    };

    const underwaterLayout = {
        ...navLayout,
        yaxis: {
            title: 'Drawdown (%)',
            gridcolor: '#1e293b',
            zerolinecolor: '#475569',
            tickformat: '.1f'
        },
        hovermode: 'x unified',
        showlegend: true,
        legend: {
            orientation: 'h',
            x: 0.5,
            xanchor: 'center',
            y: 1.15,
            bgcolor: 'rgba(15, 23, 42, 0.8)',
            bordercolor: '#334155',
            borderwidth: 1
        }
    };

    Plotly.newPlot('chart-drawdown', [strategyDDTrace, momentumDDTrace, valueDDTrace], underwaterLayout, config);

    // Chart 4: Allocation Table (replacing chart)
    renderAllocationTable(charts.allocation_series);


    // Chart 5: Rolling Returns
    const rolling3yTrace = {
        x: charts.rolling_returns.dates,
        y: charts.rolling_returns.rolling_3y,
        type: 'scatter',
        mode: 'lines',
        name: '3Y Rolling CAGR',
        line: { color: '#3b82f6', width: 2 }
    };

    const rolling5yTrace = {
        x: charts.rolling_returns.dates,
        y: charts.rolling_returns.rolling_5y,
        type: 'scatter',
        mode: 'lines',
        name: '5Y Rolling CAGR',
        line: { color: '#f59e0b', width: 2 }
    };

    Plotly.newPlot('chart-rolling', [rolling3yTrace, rolling5yTrace], navLayout, config);

    // Chart 6: Attribution
    const momContribTrace = {
        x: charts.attribution.dates,
        y: charts.attribution.mom_contrib,
        type: 'scatter',
        mode: 'lines',
        name: 'Momentum Contribution',
        line: { color: '#8b5cf6', width: 2 }
    };

    const valContribTrace = {
        x: charts.attribution.dates,
        y: charts.attribution.val_contrib,
        type: 'scatter',
        mode: 'lines',
        name: 'Value Contribution',
        line: { color: '#10b981', width: 2 }
    };

    Plotly.newPlot('chart-attribution', [momContribTrace, valContribTrace], navLayout, config);

    // Chart 7: Alpha vs Static
    const strategyNAVTrace = {
        x: charts.alpha.dates,
        y: charts.alpha.strategy_nav,
        type: 'scatter',
        mode: 'lines',
        name: 'Strategy NAV (75/25)',
        line: { color: '#8b5cf6', width: 3 }
    };

    const staticNAVTrace = {
        x: charts.alpha.dates,
        y: charts.alpha.static_nav,
        type: 'scatter',
        mode: 'lines',
        name: 'Static 50/50',
        line: { color: '#94a3b8', width: 2, dash: 'dash' }
    };

    Plotly.newPlot('chart-alpha', [staticNAVTrace, strategyNAVTrace], navLayout, config);
}

function renderCalendarReturns(calendarReturns) {
    const table = document.getElementById('calendar-returns');

    const formatReturn = (val) => {
        const sign = val >= 0 ? '+' : '';
        const cls = val >= 0 ? 'positive' : 'negative';
        return `<span class="return-value ${cls}">${sign}${val.toFixed(1)}%</span>`;
    };

    const findBest = (row) => {
        const vals = [
            { name: 'Strategy', val: row.Return },
            { name: 'Mom 30', val: row.Mom_Return },
            { name: 'Val 30', val: row.Val_Return }
        ];
        return vals.reduce((best, curr) => curr.val > best.val ? curr : best).name;
    };

    let html = `
        <thead>
            <tr>
                <th>Year</th>
                <th>Strategy</th>
                <th>Momentum 30</th>
                <th>Value 30</th>
                <th>Best</th>
            </tr>
        </thead>
        <tbody>
    `;

    calendarReturns.forEach(row => {
        const best = findBest(row);
        const strategyBest = best === 'Strategy' ? ' best-performer' : '';
        html += `
            <tr>
                <td class="year-cell">${row.Year}</td>
                <td class="${strategyBest}">${formatReturn(row.Return)}</td>
                <td class="${best === 'Mom 30' ? ' best-performer' : ''}">${formatReturn(row.Mom_Return)}</td>
                <td class="${best === 'Val 30' ? ' best-performer' : ''}">${formatReturn(row.Val_Return)}</td>
                <td class="best-cell">${best}</td>
            </tr>
        `;
    });

    html += '</tbody>';
    table.innerHTML = html;
}

function renderPortfolioHoldings(holdings, tableId) {
    const table = document.getElementById(tableId);

    const formatCurrency = (val) => {
        if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)}Cr`;
        if (val >= 100000) return `₹${(val / 100000).toFixed(2)}L`;
        if (val >= 1000) return `₹${(val / 1000).toFixed(0)}K`;
        return `₹${val.toFixed(0)}`;
    };

    let html = `
        <thead>
            <tr>
                <th>Year</th>
                <th>Month</th>
                <th>Momentum</th>
                <th>Value</th>
                <th>Cash</th>
                <th>Total Portfolio</th>
            </tr>
        </thead>
        <tbody>
    `;

    holdings.forEach(row => {
        const riskClass = row.Risk_On ? '' : 'cash-row';
        html += `
            <tr class="${riskClass}">
                <td class="year-cell">${row.Year}</td>
                <td>${row.Month}</td>
                <td>${formatCurrency(row.Momentum_Holding)}</td>
                <td>${formatCurrency(row.Value_Holding)}</td>
                <td>${formatCurrency(row.Cash_Holding)}</td>
                <td class="total-cell">${formatCurrency(row.Total_Portfolio)}</td>
            </tr>
        `;
    });

    html += '</tbody>';
    table.innerHTML = html;
}

// ==========================================
// ALLOCATION TABLE RENDERER
// ==========================================

function renderAllocationTable(allocationSeries) {
    const container = document.getElementById('allocation-table-container');

    // Organize data by year and month
    const dataByYear = {};
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    allocationSeries.dates.forEach((dateStr, index) => {
        const date = new Date(dateStr);
        const year = date.getFullYear();
        const month = date.getMonth(); // 0-11

        if (!dataByYear[year]) {
            dataByYear[year] = {};
        }

        const momValue = allocationSeries.momentum[index];
        const valValue = allocationSeries.value[index];

        dataByYear[year][month] = {
            momentum: momValue,
            value: valValue
        };
    });

    // Create table HTML
    let tableHTML = '<table class="allocation-table">';

    // Header row
    tableHTML += '<thead><tr><th class="year-col">Year</th>';
    months.forEach(month => {
        tableHTML += `<th>${month}</th>`;
    });
    tableHTML += '</tr></thead>';

    // Body rows
    tableHTML += '<tbody>';
    const years = Object.keys(dataByYear).sort();

    // Track allocation across year boundaries so January transitions are detected
    let prevAllocation = null;

    years.forEach(year => {
        tableHTML += `<tr><td class="year-col">${year}</td>`;

        months.forEach((month, monthIndex) => {
            const data = dataByYear[year][monthIndex];

            if (data) {
                const currentAllocation = `${Math.round(data.momentum)}-${Math.round(data.value)}`;
                const isChange = prevAllocation !== null && prevAllocation !== currentAllocation;
                const cellClass = isChange ? 'allocation-change' : '';

                tableHTML += `<td class="${cellClass}"><div>mom-${Math.round(data.momentum)}</div><div>val-${Math.round(data.value)}</div></td>`;
                prevAllocation = currentAllocation;
            } else {
                tableHTML += '<td class="no-data">-</td>';
            }
        });

        tableHTML += '</tr>';
    });

    tableHTML += '</tbody></table>';

    container.innerHTML = tableHTML;
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

function formatNumber(num) {
    if (num >= 10000000) {
        return `${(num / 10000000).toFixed(2)}Cr`;
    } else if (num >= 100000) {
        return `${(num / 100000).toFixed(2)}L`;
    } else if (num >= 1000) {
        return `${(num / 1000).toFixed(0)}K`;
    } else {
        return num.toFixed(0);
    }
}

// ==========================================
// NIFTY 500 INDIVIDUAL INDICES TAB
// ==========================================

async function loadNifty500IndicesData() {
    try {
        const response = await fetch('../nifty500/output/nifty500_dashboard_data.json');
        const data = await response.json();


        // Render individual index cards
        renderNifty500Indices(data.indices);

        // Load and render charts
        loadNifty500IndividualIndexCharts();
        loadNifty500RatioChart();

        // Update insights
        updateNifty500Insights(data.indices);
    } catch (error) {
        console.error('Error loading Nifty 500 indices data:', error);
    }
}

function renderNifty500Indices(indices) {
    const container = document.getElementById('nifty500-indices-container');
    container.innerHTML = '';

    indices.forEach(index => {
        const card = document.createElement('div');
        card.className = 'index-card';
        card.innerHTML = `
            <div class="index-header">
                <h3 class="index-name">${index.name}</h3>
            </div>
            <div class="index-metrics">
                <div class="metric-row">
                    <span class="metric-label">SIP XIRR</span>
                    <span class="metric-value highlight">${index.sip_xirr.toFixed(2)}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Index CAGR</span>
                    <span class="metric-value">${index.index_cagr.toFixed(2)}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Total Return</span>
                    <span class="metric-value">${index.total_return.toFixed(2)}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Invested</span>
                    <span class="metric-value">₹${index.total_invested.toLocaleString('en-IN')}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Value</span>
                    <span class="metric-value success">₹${index.final_value.toLocaleString('en-IN')}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Gain</span>
                    <span class="metric-value success">+₹${index.absolute_gain.toLocaleString('en-IN')}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Max Drawdown</span>
                    <span class="metric-value danger">${index.max_drawdown.toFixed(2)}%</span>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

async function loadNifty500IndividualIndexCharts() {
    try {
        const response = await fetch('../nifty500/output/nifty500_dashboard_data.json');
        const data = await response.json();

        if (!data.weekly_charts) {
            console.error('Weekly chart data not available for Nifty 500');
            return;
        }

        const weeklyData = data.weekly_charts;

        // Render Momentum 50 Chart
        renderIndexChart(
            'nifty500-momentum-chart',
            weeklyData.momentum.dates,
            weeklyData.momentum.close,
            weeklyData.momentum.ma_30,
            'Momentum 50 Index',
            '#8b5cf6'
        );

        // Render Value 50 Chart
        renderIndexChart(
            'nifty500-value-chart',
            weeklyData.value.dates,
            weeklyData.value.close,
            weeklyData.value.ma_30,
            'Value 50 Index',
            '#10b981'
        );

    } catch (error) {
        console.error('Error loading Nifty 500 individual index charts:', error);
    }
}

async function loadNifty500RatioChart() {
    try {
        const response = await fetch('../nifty500/output/nifty500_dashboard_data.json');
        const data = await response.json();

        if (!data.weekly_charts || !data.weekly_charts.ratio) {
            console.error('Ratio chart data not available for Nifty 500');
            return;
        }

        const ratioData = data.weekly_charts.ratio;

        const ratioTrace = {
            x: ratioData.dates,
            y: ratioData.ratio,
            type: 'scatter',
            mode: 'lines',
            name: 'Momentum/Value Ratio',
            line: { color: '#3b82f6', width: 2 }
        };

        const maTrace = {
            x: ratioData.dates,
            y: ratioData.ma_30,
            type: 'scatter',
            mode: 'lines',
            name: '30-Week MA',
            line: { color: '#f59e0b', width: 1 }
        };

        const layout = {
            autosize: true,
            xaxis: { title: 'Date', showgrid: true, gridcolor: '#1e293b', color: '#94a3b8' },
            yaxis: { title: 'Ratio', showgrid: true, gridcolor: '#1e293b', color: '#94a3b8' },
            plot_bgcolor: '#0f172a',
            paper_bgcolor: '#0f172a',
            font: { family: 'Inter, sans-serif', color: '#f1f5f9' },
            hovermode: 'x unified',
            margin: { l: 60, r: 40, t: 20, b: 60 },
            showlegend: true,
            legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.05, yanchor: 'bottom' }
        };

        Plotly.newPlot('nifty500-ratio-chart', [ratioTrace, maTrace], layout, { responsive: true });

    } catch (error) {
        console.error('Error loading Nifty 500 ratio chart:', error);
    }
}

function updateNifty500Insights(indices) {
    const bestPerformer = indices.reduce((best, current) =>
        current.sip_xirr > best.sip_xirr ? current : best
    );

    const lowestDD = indices.reduce((best, current) =>
        current.max_drawdown > best.max_drawdown ? current : best
    );

    document.getElementById('nifty500-best-performer').textContent =
        `${bestPerformer.name} with ${bestPerformer.sip_xirr.toFixed(2)}% XIRR`;

    document.getElementById('nifty500-lowest-dd').textContent =
        `${lowestDD.name} with ${lowestDD.max_drawdown.toFixed(2)}% max drawdown`;
}

// ==========================================
// NIFTY 500 PORTFOLIO STRATEGY TAB
// ==========================================

async function loadNifty500PortfolioData() {
    try {
        const response = await fetch('../nifty500/output/nifty500_portfolio_dashboard.json');
        const data = await response.json();

        // Update KPIs
        document.getElementById('nifty500-kpi-xirr').textContent = `${data.kpis.sip_xirr}%`;
        document.getElementById('nifty500-kpi-cagr').textContent = `${data.kpis.cagr}%`;
        document.getElementById('nifty500-kpi-investor-dd').textContent = `${data.kpis.max_investor_dd}%`;
        document.getElementById('nifty500-kpi-max-dd').textContent = `${data.kpis.max_drawdown}%`;
        document.getElementById('nifty500-kpi-mar').textContent = data.kpis.mar_ratio.toFixed(2);
        document.getElementById('nifty500-kpi-vol').textContent = `${data.kpis.volatility.toFixed(1)}%`;
        document.getElementById('nifty500-kpi-total-return').textContent = `${data.kpis.total_return_pct}%`;
        document.getElementById('nifty500-kpi-time-momentum').textContent = `${data.kpis.pct_time_momentum}%`;

        // Render charts
        renderNifty500NAVChart(data.charts.nav_series);
        renderNifty500SIPValueChart(data.charts.sip_value_series);
        renderNifty500DrawdownChart(data.charts.drawdown_series);
        renderNifty500AllocationTable(data.charts.allocation_series);
        renderNifty500RollingReturns(data.charts.rolling_returns);
        renderNifty500Attribution(data.charts.attribution);
        renderNifty500Alpha(data.charts.alpha);
        renderNifty500CalendarReturns(data.calendar_returns);

        // Render portfolio holdings log
        if (data.portfolio_holdings) {
            renderPortfolioHoldings(data.portfolio_holdings, 'nifty500-portfolio-holdings-table');
        }

    } catch (error) {
        console.error('Error loading Nifty 500 portfolio data:', error);
    }
}

function renderNifty500NAVChart(data) {
    const trace = {
        x: data.dates,
        y: data.nav,
        type: 'scatter',
        mode: 'lines',
        name: 'Portfolio NAV',
        line: { color: '#3b82f6', width: 2 }
    };

    const layout = {
        autosize: true,
        xaxis: { title: 'Date', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        yaxis: { title: 'NAV', type: 'log', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        plot_bgcolor: '#0f172a',
        paper_bgcolor: '#0f172a',
        font: { family: 'Inter, sans-serif', color: '#f1f5f9' },
        margin: { l: 60, r: 40, t: 20, b: 60 },
        showlegend: true,
        legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.05, yanchor: 'bottom' }
    };

    Plotly.newPlot('nifty500-chart-nav', [trace], layout, { responsive: true });
}

function renderNifty500SIPValueChart(data) {
    const investedTrace = {
        x: data.dates,
        y: data.invested,
        type: 'scatter',
        mode: 'lines',
        name: 'Total Invested',
        line: { color: '#94a3b8', width: 2, dash: 'dash' }
    };

    const valueTrace = {
        x: data.dates,
        y: data.value,
        type: 'scatter',
        mode: 'lines',
        name: 'Portfolio Value',
        line: { color: '#10b981', width: 3 }
    };

    const layout = {
        autosize: true,
        xaxis: { title: 'Date', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        yaxis: { title: 'Amount (₹)', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        plot_bgcolor: '#0f172a',
        paper_bgcolor: '#0f172a',
        font: { family: 'Inter, sans-serif', color: '#f1f5f9' },
        margin: { l: 60, r: 40, t: 20, b: 60 },
        showlegend: true,
        legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.05, yanchor: 'bottom' }
    };

    Plotly.newPlot('nifty500-chart-sip-value', [investedTrace, valueTrace], layout, { responsive: true });
}

function renderNifty500DrawdownChart(data) {
    const strategyTrace = {
        x: data.dates,
        y: data.strategy_dd,
        type: 'scatter',
        mode: 'lines',
        name: 'Strategy',
        line: { color: '#3b82f6', width: 2 },
        fill: 'tozeroy',
        fillcolor: 'rgba(59, 130, 246, 0.2)'
    };

    const momTrace = {
        x: data.dates,
        y: data.momentum_dd,
        type: 'scatter',
        mode: 'lines',
        name: 'Momentum 50',
        line: { color: '#8b5cf6', width: 1.5 }
    };

    const valTrace = {
        x: data.dates,
        y: data.value_dd,
        type: 'scatter',
        mode: 'lines',
        name: 'Value 50',
        line: { color: '#10b981', width: 1.5 }
    };

    const layout = {
        autosize: true,
        xaxis: { title: 'Date', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        yaxis: { title: 'Drawdown (%)', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        plot_bgcolor: '#0f172a',
        paper_bgcolor: '#0f172a',
        font: { family: 'Inter, sans-serif', color: '#f1f5f9' },
        margin: { l: 60, r: 40, t: 20, b: 60 },
        showlegend: true,
        legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.05, yanchor: 'bottom' }
    };

    Plotly.newPlot('nifty500-chart-drawdown', [strategyTrace, momTrace, valTrace], layout, { responsive: true });
}

function renderNifty500AllocationTable(allocationSeries) {
    const container = document.getElementById('nifty500-allocation-table-container');

    // Organize data by year and month
    const dataByYear = {};
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    allocationSeries.dates.forEach((dateStr, index) => {
        const date = new Date(dateStr);
        const year = date.getFullYear();
        const month = date.getMonth(); // 0-11

        if (!dataByYear[year]) {
            dataByYear[year] = {};
        }

        const momValue = allocationSeries.momentum[index];
        const valValue = allocationSeries.value[index];

        dataByYear[year][month] = {
            momentum: momValue,
            value: valValue
        };
    });

    // Create table HTML
    let tableHTML = '<table class="allocation-table">';

    // Header row
    tableHTML += '<thead><tr><th class="year-col">Year</th>';
    months.forEach(month => {
        tableHTML += `<th>${month}</th>`;
    });
    tableHTML += '</tr></thead>';

    // Body rows
    tableHTML += '<tbody>';
    const years = Object.keys(dataByYear).sort();

    // Track allocation across year boundaries so January transitions are detected
    let prevAllocation = null;

    years.forEach(year => {
        tableHTML += `<tr><td class="year-col">${year}</td>`;

        months.forEach((month, monthIndex) => {
            const data = dataByYear[year][monthIndex];

            if (data) {
                const currentAllocation = `${data.momentum}-${data.value}`;
                const isChange = prevAllocation !== null && prevAllocation !== currentAllocation;
                const cellClass = isChange ? 'allocation-change' : '';

                tableHTML += `<td class="${cellClass}"><div>mom-${data.momentum}</div><div>val-${data.value}</div></td>`;
                prevAllocation = currentAllocation;
            } else {
                tableHTML += '<td class="no-data">-</td>';
            }
        });

        tableHTML += '</tr>';
    });

    tableHTML += '</tbody></table>';

    container.innerHTML = tableHTML;
}

function renderNifty500RollingReturns(data) {
    const trace3y = {
        x: data.dates,
        y: data.rolling_3y,
        type: 'scatter',
        mode: 'lines',
        name: '3-Year Rolling',
        line: { color: '#3b82f6', width: 2 }
    };

    const trace5y = {
        x: data.dates,
        y: data.rolling_5y,
        type: 'scatter',
        mode: 'lines',
        name: '5-Year Rolling',
        line: { color: '#10b981', width: 2 }
    };

    const layout = {
        autosize: true,
        xaxis: { title: 'Date', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        yaxis: { title: 'CAGR (%)', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        plot_bgcolor: '#0f172a',
        paper_bgcolor: '#0f172a',
        font: { family: 'Inter, sans-serif', color: '#f1f5f9' },
        margin: { l: 60, r: 40, t: 20, b: 60 },
        showlegend: true,
        legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.05, yanchor: 'bottom' }
    };

    Plotly.newPlot('nifty500-chart-rolling', [trace3y, trace5y], layout, { responsive: true });
}

function renderNifty500Attribution(data) {
    const momTrace = {
        x: data.dates,
        y: data.mom_contrib,
        type: 'scatter',
        mode: 'lines',
        name: 'Momentum',
        line: { color: '#8b5cf6', width: 2 }
    };

    const valTrace = {
        x: data.dates,
        y: data.val_contrib,
        type: 'scatter',
        mode: 'lines',
        name: 'Value',
        line: { color: '#10b981', width: 2 }
    };

    const layout = {
        autosize: true,
        xaxis: { title: 'Date', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        yaxis: { title: 'Cumulative Contribution (%)', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        plot_bgcolor: '#0f172a',
        paper_bgcolor: '#0f172a',
        font: { family: 'Inter, sans-serif', color: '#f1f5f9' },
        margin: { l: 60, r: 40, t: 20, b: 60 },
        showlegend: true,
        legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.05, yanchor: 'bottom' }
    };

    Plotly.newPlot('nifty500-chart-attribution', [momTrace, valTrace], layout, { responsive: true });
}

function renderNifty500Alpha(data) {
    const strategyTrace = {
        x: data.dates,
        y: data.strategy_nav,
        type: 'scatter',
        mode: 'lines',
        name: 'Strategy NAV',
        line: { color: '#3b82f6', width: 2 }
    };

    const staticTrace = {
        x: data.dates,
        y: data.static_nav,
        type: 'scatter',
        mode: 'lines',
        name: 'Static 50/50',
        line: { color: '#94a3b8', width: 2, dash: 'dash' }
    };

    const layout = {
        autosize: true,
        xaxis: { title: 'Date', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        yaxis: { title: 'NAV', type: 'log', color: '#94a3b8', showgrid: true, gridcolor: '#1e293b', autorange: true },
        plot_bgcolor: '#0f172a',
        paper_bgcolor: '#0f172a',
        font: { family: 'Inter, sans-serif', color: '#f1f5f9' },
        margin: { l: 60, r: 40, t: 20, b: 60 },
        showlegend: true,
        legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.05, yanchor: 'bottom' }
    };

    Plotly.newPlot('nifty500-chart-alpha', [strategyTrace, staticTrace], layout, { responsive: true });
}

function renderNifty500CalendarReturns(returns) {
    const table = document.getElementById('nifty500-calendar-returns');

    const formatReturn = (val) => {
        const sign = val >= 0 ? '+' : '';
        const cls = val >= 0 ? 'positive' : 'negative';
        return `<span class="return-value ${cls}">${sign}${val.toFixed(1)}%</span>`;
    };

    const findBest = (row) => {
        const vals = [
            { name: 'Strategy', val: row.Return },
            { name: 'Mom 50', val: row.Mom_Return },
            { name: 'Val 50', val: row.Val_Return }
        ];
        return vals.reduce((best, curr) => curr.val > best.val ? curr : best).name;
    };

    let html = `
        <thead>
            <tr>
                <th>Year</th>
                <th>Strategy</th>
                <th>Momentum 50</th>
                <th>Value 50</th>
                <th>Best</th>
            </tr>
        </thead>
        <tbody>
    `;

    returns.forEach(row => {
        const best = findBest(row);
        const strategyBest = best === 'Strategy' ? ' best-performer' : '';
        html += `
            <tr>
                <td class="year-cell">${row.Year}</td>
                <td class="${strategyBest}">${formatReturn(row.Return)}</td>
                <td class="${best === 'Mom 50' ? ' best-performer' : ''}">${formatReturn(row.Mom_Return)}</td>
                <td class="${best === 'Val 50' ? ' best-performer' : ''}">${formatReturn(row.Val_Return)}</td>
                <td class="best-cell">${best}</td>
            </tr>
        `;
    });

    html += '</tbody>';
    table.innerHTML = html;
}

// ==========================================
// RETURNS ANALYSIS TAB
// ==========================================

async function loadReturnsAnalysis() {
    try {
        const response = await fetch('../nifty200/output/nifty200_returns_analysis.json');
        const data = await response.json();

        const CHART_DEFS = [
            // [containerId, period label, series key, title colour, fill colour]
            ['ra-mom-10y', '10Y', 'momentum', '#8b5cf6', 'rgba(139,92,246,0.15)'],
            ['ra-mom-5y', '5Y', 'momentum', '#8b5cf6', 'rgba(139,92,246,0.15)'],
            ['ra-mom-3y', '3Y', 'momentum', '#8b5cf6', 'rgba(139,92,246,0.15)'],
            ['ra-mom-1y', '1Y', 'momentum', '#8b5cf6', 'rgba(139,92,246,0.15)'],
            ['ra-val-10y', '10Y', 'value', '#10b981', 'rgba(16,185,129,0.15)'],
            ['ra-val-5y', '5Y', 'value', '#10b981', 'rgba(16,185,129,0.15)'],
            ['ra-val-3y', '3Y', 'value', '#10b981', 'rgba(16,185,129,0.15)'],
            ['ra-val-1y', '1Y', 'value', '#10b981', 'rgba(16,185,129,0.15)'],
        ];

        CHART_DEFS.forEach(([containerId, period, indexKey, lineColor, fillColor]) => {
            const series = data[indexKey][period];
            if (!series || !series.dates || series.dates.length === 0) {
                document.getElementById(containerId).innerHTML =
                    '<p style="color:#94a3b8;padding:2rem;">Insufficient data for this period.</p>';
                return;
            }
            renderCAGRChart(containerId, series.dates, series.values, period, lineColor, fillColor);
        });

    } catch (error) {
        console.error('Error loading returns analysis data:', error);
        ['ra-mom-10y', 'ra-mom-5y', 'ra-mom-3y', 'ra-mom-1y',
            'ra-val-10y', 'ra-val-5y', 'ra-val-3y', 'ra-val-1y'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.innerHTML = '<p style="color:#ef4444;padding:2rem;">Error loading chart data.</p>';
            });
    }
}

function renderCAGRChart(containerId, dates, values, periodLabel, lineColor, fillColor) {
    // Zero reference line
    const zeroLine = {
        x: [dates[0], dates[dates.length - 1]],
        y: [0, 0],
        type: 'scatter',
        mode: 'lines',
        name: '0%',
        line: { color: '#475569', width: 1, dash: 'dot' },
        showlegend: false,
        hoverinfo: 'none'
    };

    // CAGR series
    const cagrTrace = {
        x: dates,
        y: values,
        type: 'scatter',
        mode: 'lines',
        name: `${periodLabel} Rolling CAGR`,
        line: { color: lineColor, width: 2 },
        fill: 'tozeroy',
        fillcolor: fillColor,
        hovertemplate:
            '<b>Month:</b> %{x}<br>' +
            `<b>${periodLabel} CAGR:</b> %{y:.2f}%<br>` +
            '<extra></extra>'
    };

    // Compute stats for annotations
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const minV = Math.min(...values);
    const maxV = Math.max(...values);

    // Average reference line
    const avgLine = {
        x: [dates[0], dates[dates.length - 1]],
        y: [avg, avg],
        type: 'scatter',
        mode: 'lines',
        name: `Avg ${avg.toFixed(1)}%`,
        line: { color: '#f59e0b', width: 1.5, dash: 'dash' },
        hovertemplate: `<b>Average:</b> ${avg.toFixed(2)}%<extra></extra>`
    };

    const layout = {
        autosize: true,
        paper_bgcolor: '#1e293b',
        plot_bgcolor: '#1e293b',
        font: { color: '#f1f5f9', family: 'Inter, sans-serif', size: 12 },
        xaxis: {
            title: '',
            showgrid: true,
            gridcolor: '#334155',
            color: '#94a3b8',
            zeroline: false,
            tickangle: -30
        },
        yaxis: {
            title: 'CAGR (%)',
            showgrid: true,
            gridcolor: '#334155',
            color: '#94a3b8',
            zeroline: false,
            tickformat: '.1f',
            ticksuffix: '%'
        },
        hovermode: 'x unified',
        hoverlabel: {
            bgcolor: '#0f172a',
            bordercolor: '#475569',
            font: { size: 13, family: 'Inter, sans-serif', color: '#f1f5f9' }
        },
        margin: { l: 60, r: 20, t: 30, b: 50 },
        showlegend: true,
        legend: {
            orientation: 'h',
            x: 0.5,
            xanchor: 'center',
            y: 1.08,
            yanchor: 'bottom',
            bgcolor: 'rgba(15,23,42,0.7)',
            bordercolor: '#334155',
            borderwidth: 1,
            font: { size: 11 }
        },
        annotations: [
            {
                xref: 'paper', yref: 'y',
                x: 1.01, y: maxV,
                xanchor: 'left', yanchor: 'middle',
                text: `Max: ${maxV.toFixed(1)}%`,
                showarrow: false,
                font: { color: '#34d399', size: 10 }
            },
            {
                xref: 'paper', yref: 'y',
                x: 1.01, y: minV,
                xanchor: 'left', yanchor: 'middle',
                text: `Min: ${minV.toFixed(1)}%`,
                showarrow: false,
                font: { color: '#f87171', size: 10 }
            }
        ]
    };

    const config = { responsive: true, displayModeBar: true };
    Plotly.newPlot(containerId, [zeroLine, cagrTrace, avgLine], layout, config);
}

// ==========================================
// NIFTY 500 RETURNS ANALYSIS TAB
// ==========================================

async function loadNifty500ReturnsAnalysis() {
    try {
        const response = await fetch('../nifty500/output/nifty500_returns_analysis.json');
        const data = await response.json();

        const CHART_DEFS = [
            ['ra-n500-mom-10y', '10Y', 'momentum', '#8b5cf6', 'rgba(139,92,246,0.15)'],
            ['ra-n500-mom-5y', '5Y', 'momentum', '#8b5cf6', 'rgba(139,92,246,0.15)'],
            ['ra-n500-mom-3y', '3Y', 'momentum', '#8b5cf6', 'rgba(139,92,246,0.15)'],
            ['ra-n500-mom-1y', '1Y', 'momentum', '#8b5cf6', 'rgba(139,92,246,0.15)'],
            ['ra-n500-val-10y', '10Y', 'value', '#10b981', 'rgba(16,185,129,0.15)'],
            ['ra-n500-val-5y', '5Y', 'value', '#10b981', 'rgba(16,185,129,0.15)'],
            ['ra-n500-val-3y', '3Y', 'value', '#10b981', 'rgba(16,185,129,0.15)'],
            ['ra-n500-val-1y', '1Y', 'value', '#10b981', 'rgba(16,185,129,0.15)'],
        ];

        CHART_DEFS.forEach(([containerId, period, indexKey, lineColor, fillColor]) => {
            const series = data[indexKey][period];
            if (!series || !series.dates || series.dates.length === 0) {
                document.getElementById(containerId).innerHTML =
                    '<p style="color:#94a3b8;padding:2rem;">Insufficient data for this period.</p>';
                return;
            }
            renderCAGRChart(containerId, series.dates, series.values, period, lineColor, fillColor);
        });

    } catch (error) {
        console.error('Error loading Nifty 500 returns analysis data:', error);
        ['ra-n500-mom-10y', 'ra-n500-mom-5y', 'ra-n500-mom-3y', 'ra-n500-mom-1y',
            'ra-n500-val-10y', 'ra-n500-val-5y', 'ra-n500-val-3y', 'ra-n500-val-1y'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.innerHTML = '<p style="color:#ef4444;padding:2rem;">Error loading chart data.</p>';
            });
    }
}
