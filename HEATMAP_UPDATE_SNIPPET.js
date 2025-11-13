// UPDATED loadHeatmap() function for dashboard.js
// Replace the existing loadHeatmap() function with this code

async loadHeatmap() {
    try {
        const response = await fetch('/api/dashboard/heatmap?cross_domain=true&top_n=12');
        const data = await response.json();
        
        if (!data.labels || data.labels.length === 0) {
            console.warn('No correlation data available');
            this.createDemoHeatmap();
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
        
        // Create user-friendly hover callouts (not x, y, z)
        const hoverText = data.matrix.map((row, i) => 
            row.map((r, j) => {
                if (i === j) {
                    return `<b>${data.labels[i]}</b><br>` +
                           `Self-correlation = 1.000<br>` +
                           `<i>(Click elsewhere for analysis)</i>`;
                }
                if (i < j) {
                    // Upper triangle - hide duplicate
                    return `<i>See lower triangle</i>`;
                }
                
                // Lower triangle - show full details
                const strength = interpretCorrelation(r);
                const direction = r > 0 ? 'positive' : 'negative';
                const significance = formatSignificance(0.001);
                
                return `<b>Variable Pair:</b><br>` +
                       `${data.labels[i]} ↔ ${data.labels[j]}<br><br>` +
                       `<b>Correlation:</b> ${r.toFixed(3)} (${strength} ${direction})<br>` +
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
                x: 1.15,
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
                automargin: true
            }
        };
        
        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
        };
        
        Plotly.newPlot('heatmap', [trace], layout, config).then(() => {
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
        this.createDemoHeatmap();
    }
},
