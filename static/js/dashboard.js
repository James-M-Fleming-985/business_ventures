// Dashboard Data Management with Alpine.js
function dashboardData() {
    return {
        stats: {
            dataPoints: 0,
            strongCorrelations: 0,
            apiSources: 8,
            lastUpdated: '--'
        },
        availableMetrics: [],
        selectedMetric: 'all',
        networkThreshold: 0.5,
        sortBy: 'strength',
        leaderboard: [],
        
        async init() {
            console.log('Initializing dashboard...');
            await this.loadStats();
            await this.loadHeatmap();
            await this.loadTimeSeries();
            await this.loadNetwork();
            await this.loadLeaderboard();
            
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
            try {
                const response = await fetch('/api/dashboard/heatmap');
                const data = await response.json();
                
                // Create Plotly heatmap
                const trace = {
                    type: 'heatmap',
                    z: data.matrix,
                    x: data.labels,
                    y: data.labels,
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
                        title: 'r-value',
                        tickfont: { color: '#cbd5e1' },
                        titlefont: { color: '#cbd5e1' }
                    },
                    hovertemplate: '%{x} ↔ %{y}<br>r = %{z:.3f}<extra></extra>'
                };
                
                const layout = {
                    paper_bgcolor: '#1e293b',
                    plot_bgcolor: '#1e293b',
                    font: { color: '#cbd5e1' },
                    margin: { t: 40, r: 40, b: 80, l: 80 },
                    xaxis: {
                        tickangle: -45,
                        tickfont: { size: 10 },
                        gridcolor: '#475569'
                    },
                    yaxis: {
                        tickfont: { size: 10 },
                        gridcolor: '#475569'
                    }
                };
                
                const config = {
                    responsive: true,
                    displayModeBar: true,
                    displaylogo: false,
                    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
                };
                
                Plotly.newPlot('heatmap', [trace], layout, config);
                
                // Add click handler
                document.getElementById('heatmap').on('plotly_click', (eventData) => {
                    const point = eventData.points[0];
                    if (point.x !== point.y) {
                        this.openModal({ var1: point.x, var2: point.y, r: point.z });
                    }
                });
                
            } catch (error) {
                console.error('Failed to load heatmap:', error);
                this.createDemoHeatmap();
            }
        },
        
        async loadTimeSeries() {
            try {
                const response = await fetch(`/api/dashboard/timeseries?metric=${this.selectedMetric}`);
                const data = await response.json();
                
                const traces = data.series.map(series => ({
                    type: 'scatter',
                    mode: 'lines',
                    name: series.name,
                    x: series.dates,
                    y: series.values,
                    line: {
                        width: 2
                    },
                    hovertemplate: '%{y:.2f}<br>%{x}<extra></extra>'
                }));
                
                const layout = {
                    paper_bgcolor: '#1e293b',
                    plot_bgcolor: '#1e293b',
                    font: { color: '#cbd5e1' },
                    margin: { t: 20, r: 20, b: 40, l: 60 },
                    xaxis: {
                        gridcolor: '#475569',
                        showgrid: true
                    },
                    yaxis: {
                        gridcolor: '#475569',
                        showgrid: true,
                        title: 'Value'
                    },
                    showlegend: true,
                    legend: {
                        x: 0,
                        y: 1,
                        bgcolor: 'rgba(30, 41, 59, 0.8)',
                        bordercolor: '#475569',
                        borderwidth: 1
                    },
                    hovermode: 'x unified'
                };
                
                const config = {
                    responsive: true,
                    displayModeBar: true,
                    displaylogo: false
                };
                
                Plotly.newPlot('timeseries', traces, layout, config);
                
                // Update available metrics
                this.availableMetrics = data.series.map(s => s.name);
                
            } catch (error) {
                console.error('Failed to load time series:', error);
                this.createDemoTimeSeries();
            }
        },
        
        async loadNetwork() {
            try {
                const response = await fetch(`/api/dashboard/network?threshold=${this.networkThreshold}`);
                const data = await response.json();
                
                // Create network graph using Plotly
                const edgeTrace = {
                    type: 'scatter',
                    mode: 'lines',
                    x: data.edges.x,
                    y: data.edges.y,
                    line: {
                        color: '#475569',
                        width: 1
                    },
                    hoverinfo: 'none',
                    showlegend: false
                };
                
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
                    }
                };
                
                const layout = {
                    paper_bgcolor: '#1e293b',
                    plot_bgcolor: '#1e293b',
                    font: { color: '#cbd5e1' },
                    margin: { t: 20, r: 20, b: 20, l: 20 },
                    xaxis: {
                        showgrid: false,
                        zeroline: false,
                        showticklabels: false
                    },
                    yaxis: {
                        showgrid: false,
                        zeroline: false,
                        showticklabels: false
                    },
                    hovermode: 'closest'
                };
                
                const config = {
                    responsive: true,
                    displayModeBar: false
                };
                
                Plotly.newPlot('network', [edgeTrace, nodeTrace], layout, config);
                
            } catch (error) {
                console.error('Failed to load network:', error);
                this.createDemoNetwork();
            }
        },
        
        async loadLeaderboard() {
            try {
                const response = await fetch(`/api/dashboard/leaderboard?sort=${this.sortBy}`);
                const data = await response.json();
                this.leaderboard = data.correlations;
                console.log('Leaderboard loaded:', data.correlations.length, 'items');
            } catch (error) {
                console.error('Failed to load leaderboard:', error);
                this.createDemoLeaderboard();
            }
        },
        
        openModal(relationship) {
            console.log('Opening modal for:', relationship);
            // TODO: Load modal component with detailed analysis
            alert(`Detailed analysis for ${relationship.var1} ↔ ${relationship.var2}\nr = ${relationship.r?.toFixed(3) || 'N/A'}\n\n(Modal UI coming in next step)`);
        },
        
        async refreshAll() {
            console.log('Refreshing all dashboard components...');
            await Promise.all([
                this.loadStats(),
                this.loadHeatmap(),
                this.loadTimeSeries(),
                this.loadNetwork(),
                this.loadLeaderboard()
            ]);
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
