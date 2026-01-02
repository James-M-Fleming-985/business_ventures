// Dashboard Data Management with Alpine.js
function dashboardData() {
    return {
        stats: {
            dataPoints: 0,
            strongCorrelations: 0,
            apiSources: 8,
            lastUpdated: '--'
        },
        isRecalculating: false,
        isTestingCausality: false,
        causalityResults: null,
        causalityExplanation: '',
        availableMetrics: [],
        selectedMetric: 'all',
        networkThreshold: 0.5,
        sortBy: 'strength',
        leaderboard: [],
        modalOpen: false,
        modalData: {
            var1: '',
            var2: '',
            r: 0,
            p_value: '',
            strength: '',
            stability: '',
            explanation: ''
        },
        selectedDriftMetric: 'S&P 500 Index ↔ GDP Growth (%)',
        driftMetrics: {
            current: '0.85',
            forecast: '0.88',
            stability: '92',
            insight: 'Correlation trend analysis loading...'
        },
        
        async init() {
            console.log('Initializing dashboard...');
            await this.loadStats();
            await this.loadHeatmap();
            await this.loadTimeSeries();
            await this.loadNetwork();
            await this.loadLeaderboard();
            await this.loadDriftForecast();
            
            // Listen for refresh events
            window.addEventListener('dashboard-refresh', () => {
                this.refreshAll();
            });
        },
        
        async loadStats() {
            try {
                const response = await fetch('/api/dashboard/stats');
                const data = await response.json();
                this.stats = data;
                console.log('Stats loaded:', data);
            } catch (error) {
                console.error('Failed to load stats:', error);
                // Use demo data if API fails
                this.stats = {
                    dataPoints: 1250,
                    strongCorrelations: 18,
                    apiSources: 8,
                    lastUpdated: new Date().toLocaleTimeString()
                };
            }
        },
        
        async loadHeatmap() {
            console.log('📊 Loading heatmap...');
            try {
                const response = await fetch('/api/dashboard/heatmap?cross_domain=true&top_n=12');
                const data = await response.json();
                console.log('📊 Heatmap data received:', data);
                
                if (!data.labels || data.labels.length === 0) {
                    console.warn('No correlation data available:', data);
                    document.getElementById('heatmap').innerHTML = '<div class="flex items-center justify-center h-full text-slate-400"><p>No correlation data available. Click Refresh to fetch data.</p></div>';
                    return;
                }
                
                // Helper function to interpret correlation strength
                const interpretCorrelation = (r) => {
                    const abs_r = Math.abs(r);
                    if (abs_r > 0.7) return 'Strong';
                    if (abs_r > 0.4) return 'Moderate';
                    if (abs_r > 0.2) return 'Weak';
                    return 'Very weak';
                };
                
                // Helper function to format p-value with user-friendly text
                const formatSignificance = (p) => {
                    if (p < 0.001) return 'Highly Significant (p < 0.001)';
                    if (p < 0.01) return `Significant (p = ${p.toFixed(3)})`;
                    if (p < 0.05) return `Marginally Significant (p = ${p.toFixed(3)})`;
                    return `Not Significant (p = ${p.toFixed(3)})`;
                };
                
                // Create LOWER TRIANGLE matrix (eliminate duplicate pairs)
                const triangleMatrix = data.matrix.map((row, i) =>
                    row.map((val, j) => (i > j) ? val : null)  // Only show below diagonal
                );
                
                // Create user-friendly hover callouts with sample size
                const hoverText = data.matrix.map((row, i) => 
                    row.map((r, j) => {
                        if (r === null || r === undefined) {
                            return `<i>See lower triangle for this correlation</i>`;
                        }
                        
                        if (i === j) {
                            return `<b>${data.labels[i]}</b><br>` +
                                   `Self-correlation = 1.000<br>` +
                                   `<i>(Click elsewhere for analysis)</i>`;
                        }
                        
                        if (i < j) {
                            return `<i>See lower triangle</i>`;
                        }
                        
                        // Lower triangle - show full details with sample size
                        const strength = interpretCorrelation(r);
                        const direction = r > 0 ? 'positive' : 'negative';
                        const meta = data.metadata && data.metadata[i] && data.metadata[i][j] || {};
                        const sampleSize = meta.sample_size || 'N/A';
                        const pValue = meta.p_value !== undefined ? meta.p_value : 0.001;
                        const significance = formatSignificance(pValue);
                        const dateRange = meta.start_date && meta.end_date 
                            ? `${meta.start_date} to ${meta.end_date}`
                            : 'Date range unavailable';
                        
                        return `<b>Variable Pair:</b><br>` +
                               `${data.labels[i]} ↔ ${data.labels[j]}<br><br>` +
                               `<b>Correlation:</b> ${r.toFixed(3)} (${strength} ${direction})<br>` +
                               `<b>Sample Size:</b> ${sampleSize} data points<br>` +
                               `<b>Period:</b> ${dateRange}<br>` +
                               `<b>Statistical Significance:</b> ${significance}<br><br>` +
                               `<i>💡 Click to view detailed analysis with scatter plot</i>`;
                    })
                );
                
                // Create Plotly heatmap with triangle display
                const trace = {
                    type: 'heatmap',
                    z: triangleMatrix,  // Use triangle matrix instead of full matrix
                    x: data.labels,
                    y: data.labels,
                    text: hoverText,
                    hovertemplate: '%{text}<extra></extra>',
                    colorscale: [
                        [0, '#7f1d1d'],      // Strong negative - dark red
                        [0.25, '#dc2626'],   // Negative - red
                        [0.5, '#1e293b'],    // Zero - dark gray
                        [0.75, '#3b82f6'],   // Positive - blue
                        [1, '#1e3a8a']       // Strong positive - dark blue
                    ],
                    zmid: 0,
                    zmin: -1,
                    zmax: 1,
                    colorbar: {
                        title: { text: 'Correlation<br>Coefficient (r)', side: 'right' },
                        tickfont: { color: '#cbd5e1', size: 10 },
                        titlefont: { color: '#cbd5e1', size: 11 },
                        x: 1.15,  // Move colorbar away from heatmap
                        len: 0.9
                    }
                };
                
                const layout = {
                    title: {
                        text: 'Top Cross-Domain Correlations (Triangle View)',
                        font: { color: '#cbd5e1', size: 14 }
                    },
                    paper_bgcolor: '#1e293b',
                    plot_bgcolor: '#1e293b',
                    font: { color: '#cbd5e1' },
                    margin: { t: 60, r: 120, b: 100, l: 140 },
                    xaxis: {
                        tickangle: -45,
                        tickfont: { size: 11 },
                        gridcolor: '#475569',
                        side: 'bottom'
                    },
                    yaxis: {
                        tickfont: { size: 11 },
                        gridcolor: '#475569',
                        automargin: true  // Prevent label cutoff
                    }
                };
                
                const config = {
                    responsive: true,
                    displayModeBar: true,
                    displaylogo: false,
                    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
                };
                
                console.log('📊 Rendering heatmap with Plotly...');
                Plotly.newPlot('heatmap', [trace], layout, config).then(() => {
                    console.log('✅ Heatmap rendered successfully');
                    // Add click handler after plot is created
                    const heatmapDiv = document.getElementById('heatmap');
                    const self = this; // Preserve context
                    
                    heatmapDiv.on('plotly_click', function(eventData) {
                        const point = eventData.points[0];
                        console.log('Heatmap clicked:', {
                            variable1: point.y,
                            variable2: point.x,
                            correlation: point.z
                        });
                        
                        // Only open modal for lower triangle (i > j) and not diagonal
                        if (point.x !== point.y && point.z !== null) {
                            self.openModal({ 
                                var1: point.y,  // y-axis variable
                                var2: point.x,  // x-axis variable
                                r: point.z 
                            });
                        }
                    });
                });
                
            } catch (error) {
                console.error('Failed to load heatmap:', error);
                document.getElementById('heatmap').innerHTML = '<div class="flex items-center justify-center h-full text-slate-400"><p>Error loading heatmap: ' + error.message + '</p></div>';
            }
        },
        
        async loadTimeSeries() {
            console.log('📈 Loading time series...');
            try {
                const response = await fetch('/api/dashboard/top-variables-timeseries?limit=5');
                const data = await response.json();
                console.log('📈 Time series data received:', data);
                
                if (!data.series || data.series.length === 0) {
                    console.warn('No time series data available:', data.message);
                    document.getElementById('timeseries').innerHTML = '<div class="flex items-center justify-center h-full text-slate-400"><p>No time series data available. ' + (data.message || 'Click Refresh to fetch data.') + '</p></div>';
                    return;
                }
                
                // Create one trace per variable with normalized Y-axis
                const traces = data.series.map(series => {
                    // Format raw values for hover text
                    const formattedValues = series.raw_values.map(val => {
                        return this.formatValue(val, series.unit);
                    });
                    
                    return {
                        type: 'scatter',
                        mode: 'lines',
                        name: series.name,
                        x: series.dates,
                        y: series.values,  // Normalized 0-1 values
                        text: formattedValues,  // Raw formatted values for hover
                        line: {
                            width: 2
                        },
                        hovertemplate: '%{text}<br>%{x}<extra></extra>'
                    };
                });
                
                const layout = {
                    paper_bgcolor: '#1e293b',
                    plot_bgcolor: '#1e293b',
                    font: { color: '#cbd5e1' },
                    margin: { t: 20, r: 20, b: 60, l: 70 },
                    xaxis: {
                        gridcolor: '#475569',
                        showgrid: true,
                        title: { text: 'Date', font: { size: 11 } }
                    },
                    yaxis: {
                        gridcolor: '#475569',
                        showgrid: true,
                        title: { text: 'Normalized (0-1 scale)', font: { size: 11 } },
                        range: [0, 1]
                    },
                    showlegend: true,
                    legend: {
                        x: 0.5,
                        y: -0.25,
                        xanchor: 'center',
                        yanchor: 'top',
                        orientation: 'horizontal',
                        bgcolor: 'rgba(30, 41, 59, 0.9)',
                        bordercolor: '#475569',
                        borderwidth: 1,
                        font: { size: 10 }
                    },
                    hovermode: 'closest'
                };
                
                const config = {
                    responsive: true,
                    displayModeBar: true,
                    displaylogo: false
                };
                
                console.log('📈 Rendering time series with Plotly...');
                Plotly.newPlot('timeseries', traces, layout, config).then(() => {
                    console.log('✅ Time series rendered successfully');
                }).catch(err => {
                    console.error('❌ Time series rendering failed:', err);
                });
                
            } catch (error) {
                console.error('Failed to load time series:', error);
            }
        },
        
        async loadNetwork() {
            try {
                const response = await fetch(`/api/dashboard/network?threshold=${this.networkThreshold}`);
                const data = await response.json();
                
                // Check for errors or empty data
                if (data.error || !data.edges || !data.nodes) {
                    console.warn('Network data unavailable:', data.message || data.error);
                    this.createDemoNetwork();
                    return;
                }
                
                // Create edge trace (lines connecting nodes)
                const edgeTrace = {
                    type: 'scatter',
                    mode: 'lines',
                    x: data.edges.x,
                    y: data.edges.y,
                    line: {
                        color: '#475569',
                        width: 2
                    },
                    hoverinfo: 'none',
                    showlegend: false  // Hide from legend
                };
                
                // Create node trace (variables as circles)
                const nodeTrace = {
                    type: 'scatter',
                    mode: 'markers+text',
                    x: data.nodes.x,
                    y: data.nodes.y,
                    text: data.nodes.labels,
                    textposition: 'top center',
                    marker: {
                        size: data.nodes.sizes,
                        color: data.nodes.colors,
                        line: {
                            color: '#cbd5e1',
                            width: 2
                        }
                    },
                    hovertemplate: '%{text}<br>Connections: %{marker.size}<extra></extra>',
                    textfont: {
                        size: 10,
                        color: '#cbd5e1'
                    },
                    showlegend: false  // Hide from legend
                };
                
                const layout = {
                    paper_bgcolor: '#1e293b',
                    plot_bgcolor: '#1e293b',
                    font: { color: '#cbd5e1' },
                    margin: { t: 20, r: 20, b: 20, l: 20 },
                    xaxis: {
                        showgrid: false,
                        zeroline: false,
                        showticklabels: false,
                        range: [-1.5, 1.5]
                    },
                    yaxis: {
                        showgrid: false,
                        zeroline: false,
                        showticklabels: false,
                        range: [-1.5, 1.5]
                    },
                    hovermode: 'closest',
                    showlegend: false
                };
                
                const config = {
                    responsive: true,
                    displayModeBar: false
                };
                
                // Use Plotly.react for smooth updates (no flickering)
                Plotly.react('network', [edgeTrace, nodeTrace], layout, config);
                
            } catch (error) {
                console.error('Failed to load network:', error);
                this.createDemoNetwork();
            }
        },
        
        async loadLeaderboard() {
            try {
                const response = await fetch(`/api/dashboard/leaderboard?sort=${this.sortBy}`);
                const data = await response.json();
                
                // Check for errors or empty data
                if (data.error || !data.leaderboard || !Array.isArray(data.leaderboard)) {
                    console.warn('Leaderboard data unavailable:', data.error);
                    this.createDemoLeaderboard();
                    return;
                }
                
                this.leaderboard = data.leaderboard;
                console.log('Leaderboard loaded:', data.leaderboard.length, 'items');
            } catch (error) {
                console.error('Failed to load leaderboard:', error);
                this.createDemoLeaderboard();
            }
        },
        
        async openModal(relationship) {
            console.log('Opening modal for:', relationship);
            
            // Reset causality results when opening new modal
            this.causalityResults = null;
            this.causalityExplanation = '';
            
            try {
                // Get detailed relationship data from API
                const var1 = relationship.var1 || relationship.variable_1 || relationship.variable1;
                const var2 = relationship.var2 || relationship.variable_2 || relationship.variable2;
                
                const response = await fetch(`/api/dashboard/relationship/${encodeURIComponent(var1)}/${encodeURIComponent(var2)}`);
                const data = await response.json();
                
                // Check for API error
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Set modal data from API response
                this.modalData = {
                    var1: data.var1 || var1,
                    var2: data.var2 || var2,
                    r: data.correlation || 0,
                    p_value: data.p_value < 0.001 ? '< 0.001' : data.p_value.toFixed(4),
                    strength: (data.strength || 'moderate').charAt(0).toUpperCase() + (data.strength || 'moderate').slice(1),
                    stability: data.stability || 'stable',
                    explanation: data.explanation || 'Correlation analysis',
                    scatterData: data.scatter_data || [],
                    timeseriesData: data.timeseries || null
                };
                
                // Open modal
                this.modalOpen = true;
                
                // Wait for modal to render, then create charts
                setTimeout(() => {
                    this.createModalCharts();
                }, 100);
                
            } catch (error) {
                console.error('Failed to load relationship details:', error);
                
                // Fallback to demo data
                const var1 = relationship.var1 || relationship.variable_1 || relationship.variable1 || 'Variable 1';
                const var2 = relationship.var2 || relationship.variable_2 || relationship.variable2 || 'Variable 2';
                const r = relationship.r || relationship.correlation || 0;
                
                this.modalData = {
                    var1: var1,
                    var2: var2,
                    r: r,
                    p_value: '< 0.001',
                    strength: Math.abs(r) > 0.7 ? 'Strong' : Math.abs(r) > 0.4 ? 'Moderate' : 'Weak',
                    stability: '92%',
                    explanation: `There is a correlation between ${var1} and ${var2}.`,
                    scatterData: null,
                    timeseriesData: null
                };
                
                this.modalOpen = true;
                setTimeout(() => {
                    this.createModalCharts();
                }, 100);
            }
        },
        
        formatValue(value, unit) {
            // Helper function to format values with proper units and currency
            
            // Currency conversion (USD to GBP, approximate rate)
            const USD_TO_GBP = 0.79;
            
            if (!unit) {
                // No unit, just format number
                return this.formatLargeNumber(value);
            }
            
            // Handle USD currency - convert to GBP
            if (unit === 'USD') {
                const gbpValue = value * USD_TO_GBP;
                return '£' + this.formatLargeNumber(gbpValue);
            }
            
            // Handle other units
            const formattedNum = this.formatLargeNumber(value);
            
            // Add unit suffix based on type
            if (unit === 'count') {
                return formattedNum;  // Just the number
            } else if (unit === '%') {
                return formattedNum + '%';
            } else {
                return formattedNum + ' ' + unit;
            }
        },
        
        formatLargeNumber(value) {
            // Format large numbers with M, Bn, T abbreviations
            const absValue = Math.abs(value);
            const sign = value < 0 ? '-' : '';
            
            if (absValue >= 1e12) {
                // Trillions
                return sign + (absValue / 1e12).toFixed(2) + 'T';
            } else if (absValue >= 1e9) {
                // Billions
                return sign + (absValue / 1e9).toFixed(2) + 'Bn';
            } else if (absValue >= 1e6) {
                // Millions
                return sign + (absValue / 1e6).toFixed(2) + 'M';
            } else if (absValue >= 1e3) {
                // Thousands
                return sign + (absValue / 1e3).toFixed(2) + 'K';
            } else {
                // Less than 1000
                return sign + absValue.toFixed(2);
            }
        },
        
        createModalCharts() {
            // Scatter plot - use real data if available
            let scatterX, scatterY;
            
            if (this.modalData.scatterData && this.modalData.scatterData.length > 0) {
                // Use real API data
                scatterX = this.modalData.scatterData.map(d => d.x);
                scatterY = this.modalData.scatterData.map(d => d.y);
            } else {
                // Fallback to demo data
                scatterX = Array.from({length: 30}, () => Math.random() * 100 + 50);
                scatterY = scatterX.map(x => x * 0.85 + Math.random() * 20);
            }
            
            const scatterData = [{
                type: 'scatter',
                mode: 'markers',
                x: scatterX,
                y: scatterY,
                marker: {
                    size: 8,
                    color: '#3b82f6',
                    opacity: 0.6
                }
            }];
            
            const scatterLayout = {
                paper_bgcolor: '#0f172a',
                plot_bgcolor: '#1e293b',
                font: { color: '#cbd5e1' },
                margin: { t: 20, r: 20, b: 40, l: 50 },
                xaxis: { title: this.modalData.var1, gridcolor: '#475569' },
                yaxis: { title: this.modalData.var2, gridcolor: '#475569' }
            };
            
            Plotly.newPlot('modalScatter', scatterData, scatterLayout, {displayModeBar: false, responsive: true});
            
            // Time series overlay - use real data if available
            let dates, series1Data, series2Data, series1Raw, series2Raw, var1Unit, var2Unit;
            
            if (this.modalData.timeseriesData && this.modalData.timeseriesData.dates) {
                // Use real API data (normalized for chart, raw for hover)
                dates = this.modalData.timeseriesData.dates;
                series1Data = this.modalData.timeseriesData.var1_values;  // Normalized 0-1
                series2Data = this.modalData.timeseriesData.var2_values;  // Normalized 0-1
                series1Raw = this.modalData.timeseriesData.var1_raw;      // Actual values
                series2Raw = this.modalData.timeseriesData.var2_raw;      // Actual values
                var1Unit = this.modalData.timeseriesData.var1_unit;       // Unit (USD, count, etc.)
                var2Unit = this.modalData.timeseriesData.var2_unit;       // Unit
            } else {
                // Fallback to demo data
                dates = Array.from({length: 30}, (_, i) => {
                    const d = new Date();
                    d.setDate(d.getDate() - (30 - i));
                    return d.toISOString().split('T')[0];
                });
                series1Data = Array.from({length: 30}, (_, i) => 100 + Math.sin(i/5) * 20);
                series2Data = Array.from({length: 30}, (_, i) => 100 + Math.sin(i/5) * 20 * 0.8);
                series1Raw = series1Data;  // Use same for demo
                series2Raw = series2Data;
                var1Unit = null;
                var2Unit = null;
            }
            
            // Format the hover text with proper units and abbreviations
            const series1Formatted = series1Raw.map(val => this.formatValue(val, var1Unit));
            const series2Formatted = series2Raw.map(val => this.formatValue(val, var2Unit));
            
            const tsData = [
                {
                    type: 'scatter',
                    mode: 'lines',
                    name: this.modalData.var1,
                    x: dates,
                    y: series1Data,  // Plot normalized values
                    text: series1Formatted,  // Store formatted text
                    hovertemplate: '<b>%{fullData.name}</b><br>' +
                                   'Date: %{x}<br>' +
                                   'Value: %{text}<br>' +
                                   '<extra></extra>',
                    line: { color: '#3b82f6', width: 2 }
                },
                {
                    type: 'scatter',
                    mode: 'lines',
                    name: this.modalData.var2,
                    x: dates,
                    y: series2Data,  // Plot normalized values
                    text: series2Formatted,  // Store formatted text
                    hovertemplate: '<b>%{fullData.name}</b><br>' +
                                   'Date: %{x}<br>' +
                                   'Value: %{text}<br>' +
                                   '<extra></extra>',
                    line: { color: '#10b981', width: 2 }
                }
            ];
            
            const tsLayout = {
                paper_bgcolor: '#0f172a',
                plot_bgcolor: '#1e293b',
                font: { color: '#cbd5e1', size: 10 },
                margin: { t: 20, r: 20, b: 40, l: 50 },
                xaxis: { 
                    gridcolor: '#475569',
                    type: 'date',
                    range: [dates[0], dates[dates.length - 1]]  // Show full date range
                },
                yaxis: { 
                    gridcolor: '#475569',
                    title: 'Normalized Values (0-1)',
                    range: [0, 1]
                },
                showlegend: true,
                legend: { x: 0, y: 1, bgcolor: 'rgba(30, 41, 59, 0.8)' }
            };
            
            Plotly.newPlot('modalTimeSeries', tsData, tsLayout, {displayModeBar: false, responsive: true});
        },
        
        async loadDriftForecast() {
            try {
                // Parse selected metric
                const [var1, var2] = this.selectedDriftMetric.split(' ↔ ');
                
                // Fetch time series data from API
                const tsResponse = await fetch('/api/dashboard/timeseries');
                const tsData = await tsResponse.json();
                
                // Find the two series by name
                const series1 = tsData.series.find(s => s.name === var1);
                const series2 = tsData.series.find(s => s.name === var2);
                
                if (!series1 || !series2) {
                    console.warn('Could not find series for:', var1, var2);
                    this.loadDemoForecast();
                    return;
                }
                
                // Calculate rolling correlation (30-day window)
                const windowSize = 30;
                const rollingCorrelations = [];
                const correlationDates = [];
                
                for (let i = windowSize; i < series1.values.length; i++) {
                    const window1 = series1.values.slice(i - windowSize, i);
                    const window2 = series2.values.slice(i - windowSize, i);
                    
                    // Calculate Pearson correlation
                    const n = window1.length;
                    const mean1 = window1.reduce((a, b) => a + b) / n;
                    const mean2 = window2.reduce((a, b) => a + b) / n;
                    
                    let numerator = 0;
                    let sum1Sq = 0;
                    let sum2Sq = 0;
                    
                    for (let j = 0; j < n; j++) {
                        const diff1 = window1[j] - mean1;
                        const diff2 = window2[j] - mean2;
                        numerator += diff1 * diff2;
                        sum1Sq += diff1 * diff1;
                        sum2Sq += diff2 * diff2;
                    }
                    
                    const correlation = numerator / Math.sqrt(sum1Sq * sum2Sq);
                    rollingCorrelations.push(correlation);
                    correlationDates.push(series1.dates[i]);
                }
                
                // Use last 30 correlation values for forecasting
                const historical = rollingCorrelations.slice(-30);
                
                // Call forecast API with correlation time series
                const forecastResponse = await fetch('/api/v1/forecast', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        data: historical,
                        horizon: 30,
                        model_type: 'ensemble',
                        confidence_level: 0.95
                    })
                });
                
                const forecastData = await forecastResponse.json();
                const forecast = forecastData.forecast.values;
                const lowerCI = forecastData.forecast.confidence_intervals.lower;
                const upperCI = forecastData.forecast.confidence_intervals.upper;
                
                // Clamp forecast values to valid correlation range [-1, 1]
                const clampedForecast = forecast.map(v => Math.max(-1, Math.min(1, v)));
                const clampedLower = lowerCI.map(v => Math.max(-1, Math.min(1, v)));
                const clampedUpper = upperCI.map(v => Math.max(-1, Math.min(1, v)));
                
                // Generate dates
                const historicalDates = correlationDates.slice(-30);
                const forecastDates = Array.from({length: 30}, (_, i) => {
                    const d = new Date(correlationDates[correlationDates.length - 1]);
                    d.setDate(d.getDate() + i + 1);
                    return d.toISOString().split('T')[0];
                });
                
                // Historical trace
                const historicalTrace = {
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Historical r',
                    x: historicalDates,
                    y: historical,
                    line: { color: '#3b82f6', width: 3 }
                };
                
                // Forecast trace
                const forecastTrace = {
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Forecast r',
                    x: forecastDates,
                    y: clampedForecast,
                    line: { color: '#10b981', width: 3, dash: 'dash' }
                };
                
                // Confidence interval
                const confidenceTrace = {
                    type: 'scatter',
                    mode: 'none',
                    name: '95% CI',
                    x: [...forecastDates, ...forecastDates.slice().reverse()],
                    y: [...clampedUpper, ...clampedLower.slice().reverse()],
                    fill: 'toself',
                    fillcolor: 'rgba(16, 185, 129, 0.2)',
                    line: { width: 0 }
                };
                
                const layout = {
                    paper_bgcolor: '#1e293b',
                    plot_bgcolor: '#1e293b',
                    font: { color: '#cbd5e1' },
                    margin: { t: 20, r: 20, b: 40, l: 60 },
                    xaxis: { 
                        gridcolor: '#475569',
                        title: 'Date'
                    },
                    yaxis: { 
                        gridcolor: '#475569',
                        title: 'Correlation Coefficient (r)',
                        range: [-1, 1]
                    },
                    showlegend: true,
                    legend: { 
                        x: 0.02, 
                        y: 0.98,
                        bgcolor: 'rgba(30, 41, 59, 0.9)',
                        font: { size: 10 }
                    }
                };
                
                Plotly.newPlot('driftChart', [confidenceTrace, historicalTrace, forecastTrace], layout, {
                    responsive: true,
                    displayModeBar: false
                });
                
                // Update metrics based on forecast
                const currentValue = historical[historical.length-1];
                const forecastValue = clampedForecast[clampedForecast.length-1];
                const absoluteChange = forecastValue - currentValue;
                const percentChange = (absoluteChange / Math.abs(currentValue) * 100).toFixed(1);
                
                // Calculate stability as inverse of coefficient of variation
                const historicalMean = historical.reduce((a, b) => a + b) / historical.length;
                const historicalStd = Math.sqrt(historical.reduce((sum, val) => sum + Math.pow(val - historicalMean, 2), 0) / historical.length);
                const cv = (historicalStd / Math.abs(historicalMean)) * 100;
                const stability = Math.max(0, 100 - cv).toFixed(0);
                
                // Determine trend direction and message
                let insight;
                if (absoluteChange > 0.05) {
                    insight = `Strengthening trend (+${Math.abs(percentChange)}%). Correlation expected to increase.`;
                } else if (absoluteChange < -0.05) {
                    insight = `Weakening trend (${percentChange}%). Correlation expected to decrease.`;
                } else {
                    insight = 'Stable trend. Correlation expected to remain relatively constant.';
                }
                
                this.driftMetrics = {
                    current: currentValue.toFixed(2),
                    forecast: forecastValue.toFixed(2),
                    stability: stability,
                    insight: insight
                };
                
            } catch (error) {
                console.error('Failed to load drift forecast:', error);
                // Fallback to demo visualization on error
                this.loadDemoForecast();
            }
        },
        
        loadDemoForecast() {
            // Fallback demo forecast when API fails
            const historical = Array.from({length: 30}, (_, i) => 0.8 + Math.sin(i/10) * 0.1 + Math.random() * 0.05);
            const forecast = Array.from({length: 30}, (_, i) => historical[historical.length-1] + i * 0.003 + Math.random() * 0.02);
            
            const dates = Array.from({length: 60}, (_, i) => {
                const d = new Date();
                d.setDate(d.getDate() - (30 - i));
                return d.toISOString().split('T')[0];
            });
            
            const historicalTrace = {
                type: 'scatter',
                mode: 'lines',
                name: 'Historical',
                x: dates.slice(0, 30),
                y: historical,
                line: { color: '#3b82f6', width: 3 }
            };
            
            const forecastTrace = {
                type: 'scatter',
                mode: 'lines',
                name: 'Forecast',
                x: dates.slice(30),
                y: forecast,
                line: { color: '#10b981', width: 3, dash: 'dash' }
            };
            
            const upperBound = forecast.map(v => v + 0.05);
            const lowerBound = forecast.map(v => v - 0.05);
            
            const confidenceTrace = {
                type: 'scatter',
                mode: 'none',
                name: '95% Confidence',
                x: [...dates.slice(30), ...dates.slice(30).reverse()],
                y: [...upperBound, ...lowerBound.reverse()],
                fill: 'toself',
                fillcolor: 'rgba(16, 185, 129, 0.2)',
                line: { width: 0 }
            };
            
            const layout = {
                paper_bgcolor: '#1e293b',
                plot_bgcolor: '#1e293b',
                font: { color: '#cbd5e1' },
                margin: { t: 20, r: 20, b: 40, l: 60 },
                xaxis: { gridcolor: '#475569', title: 'Date' },
                yaxis: { gridcolor: '#475569', title: 'Value' },
                showlegend: true,
                legend: { x: 0.02, y: 0.98, bgcolor: 'rgba(30, 41, 59, 0.9)', font: { size: 10 } }
            };
            
            Plotly.newPlot('driftChart', [confidenceTrace, historicalTrace, forecastTrace], layout, {
                responsive: true,
                displayModeBar: false
            });
            
            this.driftMetrics = {
                current: historical[historical.length-1].toFixed(2),
                forecast: forecast[forecast.length-1].toFixed(2),
                stability: '92',
                insight: 'Demo mode: Using simulated forecast data.'
            };
        },
        
        exportAnalysis() {
            console.log('Exporting analysis for:', this.modalData.var1, '↔', this.modalData.var2);
            alert('Export functionality coming soon! Will generate PDF report with full analysis.');
        },
        
        async refreshAll() {
            console.log('Refreshing all dashboard components...');
            await Promise.all([
                this.loadStats(),
                this.loadHeatmap(),
                this.loadTimeSeries(),
                this.loadNetwork(),
                this.loadLeaderboard(),
                this.loadDriftForecast()
            ]);
        },
        
        async recalculateCorrelations() {
            if (this.isRecalculating) return;
            
            if (!confirm('This will recalculate all correlations with proper date ranges. This may take 1-2 minutes. Continue?')) {
                return;
            }
            
            this.isRecalculating = true;
            console.log('Starting correlation recalculation...');
            
            try {
                const response = await fetch('/api/admin/calculate-correlations', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                console.log('Recalculation complete:', data);
                alert(`Success! Recalculated ${data.total_calculated || 'all'} correlations. The scatter plots will now show the correct data points.`);
                
                // Refresh dashboard after recalculation
                await this.refreshAll();
                
            } catch (error) {
                console.error('Recalculation failed:', error);
                alert('Failed to recalculate correlations: ' + error.message);
            } finally {
                this.isRecalculating = false;
            }
        },
        
        async testCausality() {
            if (this.isTestingCausality) return;
            
            this.isTestingCausality = true;
            console.log('Testing Granger causality for:', this.modalData.var1, '↔', this.modalData.var2);
            
            try {
                const response = await fetch(
                    `/api/dashboard/causality/${encodeURIComponent(this.modalData.var1)}/${encodeURIComponent(this.modalData.var2)}`,
                    { method: 'POST' }
                );
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Causality test failed');
                }
                
                const data = await response.json();
                console.log('Causality results:', data);
                
                this.causalityResults = data;
                this.causalityExplanation = data.explanation || 'Causality analysis complete';
                
                // Scroll to results
                setTimeout(() => {
                    document.querySelector('.space-y-3')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
                
            } catch (error) {
                console.error('Causality test failed:', error);
                alert('Failed to test causality: ' + error.message);
            } finally {
                this.isTestingCausality = false;
            }
        },
        
        // Demo data functions (fallback if API not ready)
        createDemoHeatmap() {
            const labels = ['GDP', 'Stock Market', 'Temperature', 'Earthquakes', 'Research Papers'];
            const matrix = [
                [1.0, 0.85, 0.42, -0.12, 0.68],
                [0.85, 1.0, 0.38, -0.08, 0.72],
                [0.42, 0.38, 1.0, 0.05, 0.15],
                [-0.12, -0.08, 0.05, 1.0, -0.03],
                [0.68, 0.72, 0.15, -0.03, 1.0]
            ];
            
            const trace = {
                type: 'heatmap',
                z: matrix,
                x: labels,
                y: labels,
                colorscale: [
                    [0, '#7f1d1d'],
                    [0.25, '#dc2626'],
                    [0.5, '#1e293b'],
                    [0.75, '#3b82f6'],
                    [1, '#1e3a8a']
                ],
                zmid: 0,
                zmin: -1,
                zmax: 1,
                colorbar: {
                    title: 'r-value',
                    tickfont: { color: '#cbd5e1' },
                    titlefont: { color: '#cbd5e1' }
                }
            };
            
            const layout = {
                paper_bgcolor: '#1e293b',
                plot_bgcolor: '#1e293b',
                font: { color: '#cbd5e1' },
                margin: { t: 40, r: 40, b: 80, l: 80 }
            };
            
            Plotly.newPlot('heatmap', [trace], layout, { responsive: true, displaylogo: false });
        },
        
        createDemoTimeSeries() {
            const dates = Array.from({length: 30}, (_, i) => {
                const d = new Date();
                d.setDate(d.getDate() - 29 + i);
                return d.toISOString().split('T')[0];
            });
            
            const trace1 = {
                type: 'scatter',
                mode: 'lines',
                name: 'GDP Growth',
                x: dates,
                y: dates.map((_, i) => 2.5 + Math.sin(i / 5) + Math.random() * 0.5),
                line: { width: 2, color: '#3b82f6' }
            };
            
            const trace2 = {
                type: 'scatter',
                mode: 'lines',
                name: 'Stock Index',
                x: dates,
                y: dates.map((_, i) => 3.0 + Math.cos(i / 4) + Math.random() * 0.6),
                line: { width: 2, color: '#d946ef' }
            };
            
            const layout = {
                paper_bgcolor: '#1e293b',
                plot_bgcolor: '#1e293b',
                font: { color: '#cbd5e1' },
                margin: { t: 20, r: 20, b: 40, l: 60 },
                xaxis: { gridcolor: '#475569' },
                yaxis: { gridcolor: '#475569', title: 'Value' },
                showlegend: true,
                legend: { bgcolor: 'rgba(30, 41, 59, 0.8)' }
            };
            
            Plotly.newPlot('timeseries', [trace1, trace2], layout, { responsive: true, displaylogo: false });
            this.availableMetrics = ['GDP Growth', 'Stock Index'];
        },
        
        createDemoNetwork() {
            // Simple network layout
            const nodes = 5;
            const angles = Array.from({length: nodes}, (_, i) => (i * 2 * Math.PI) / nodes);
            const x = angles.map(a => Math.cos(a));
            const y = angles.map(a => Math.sin(a));
            
            const edgeTrace = {
                type: 'scatter',
                mode: 'lines',
                x: [x[0], x[1], null, x[1], x[2], null, x[2], x[3]],
                y: [y[0], y[1], null, y[1], y[2], null, y[2], y[3]],
                line: { color: '#475569', width: 1 },
                hoverinfo: 'none'
            };
            
            const nodeTrace = {
                type: 'scatter',
                mode: 'markers+text',
                x: x,
                y: y,
                text: ['GDP', 'Stocks', 'Temp', 'Quakes', 'Papers'],
                textposition: 'top center',
                marker: { size: [30, 28, 20, 15, 25], color: '#3b82f6', line: { color: '#cbd5e1', width: 2 } },
                textfont: { color: '#cbd5e1' }
            };
            
            const layout = {
                paper_bgcolor: '#1e293b',
                plot_bgcolor: '#1e293b',
                showlegend: false,
                xaxis: { showgrid: false, zeroline: false, showticklabels: false },
                yaxis: { showgrid: false, zeroline: false, showticklabels: false },
                margin: { t: 20, r: 20, b: 20, l: 20 }
            };
            
            Plotly.newPlot('network', [edgeTrace, nodeTrace], layout, { responsive: true, displayModeBar: false });
        },
        
        createDemoLeaderboard() {
            this.leaderboard = [
                { var1: 'GDP', var2: 'Stock Market', r: 0.85, p: 0.001 },
                { var1: 'GDP', var2: 'Research Papers', r: 0.72, p: 0.003 },
                { var1: 'Stock Market', var2: 'Research Papers', r: 0.68, p: 0.005 },
                { var1: 'GDP', var2: 'Temperature', r: 0.42, p: 0.025 },
                { var1: 'Stock Market', var2: 'Temperature', r: 0.38, p: 0.032 },
                { var1: 'Temperature', var2: 'Research Papers', r: 0.15, p: 0.154 },
                { var1: 'GDP', var2: 'Earthquakes', r: -0.12, p: 0.245 }
            ];
        }
    };
}
