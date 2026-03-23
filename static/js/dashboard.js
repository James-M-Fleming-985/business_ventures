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
        
        // ============================================================
        // SIGNAL RADAR: Layer 1 Fast Signals → Layer 2 Predictions
        // ============================================================
        activeView: 'cascade',  // 'cascade', 'heatmap', 'network', 'leaderboard'
        fastSignals: [],        // Layer 1 signals with momentum
        filteredSignals: [],    // Filtered version based on dropdown
        signalFilter: 'top10',  // Filter: top10, top20, rising, falling, all
        selectedFastSignal: null,
        predictedOutcomes: [],  // Layer 2 predictions based on selected signal
        selectedCascade: null,
        topInsight: null,
        
        // Signal Detail Modal State
        signalModalOpen: false,
        signalModalData: {
            keyword: '',
            momentum: 0,
            source_count: 1,
            agreement_score: 0,
            confidence: 0,
            confidence_level: '',
            sources: []
        },
        
        // Granger Analysis State (for modal)
        signalGrangerResults: null,
        isRunningSignalGranger: false,
        
        // Deep Analysis State (lag curve, regression, prediction)
        deepAnalysis: null,
        isRunningDeepAnalysis: false,
        
        // ============================================================
        // EXPLOITATION BOARD
        // ============================================================
        exploitationRecommendations: [],
        filteredExploitation: [],
        exploitationFilterAction: '',
        exploitationFilterStatus: '',
        isGeneratingRecommendations: false,
        exploitationStats: { total: 0, by_action_type: {}, avg_score: 0 },

        // ============================================================
        // PREDICTION ACCURACY TRACKING (CA-002-10)
        // ============================================================
        predictionServiceAvailable: true,
        predictionMetrics: {
            total_predictions: 0,
            pending: 0,
            validated: 0,
            pair_count: 0,
            direction_accuracy: null,
            avg_error_pct: null,
            avg_lag_error_days: null,
            avg_change_error_pct: null
        },
        predictionTimeseries: [],
        timeSeriesData: [],
        predictionLayers: {
            storage: false,
            updater: false,
            analytics: false
        },
        isUpdatingActuals: false,
        recentPredictions: [],
        predictionFilter: '',
        
        // ============================================================
        // PROGRAMME BASELINES (M0)
        // ============================================================
        baselines: null,
        baselinesLoading: false,

        // ============================================================
        // REVENUE DASHBOARD (M1 Track E)
        // ============================================================
        revenueData: null,
        revenueLoading: false,
        
        // Exploitation Validation Modal
        validationModalOpen: false,
        validationRecId: null,
        validationRecName: '',
        validationForm: {
            actual_outcome: 'UNKNOWN',
            outcome_notes: '',
            demand_accurate: null,
            competition_accurate: null,
            revenue_potential_accurate: null,
            actual_revenue: null,
        },

        // MVP Build state
        builds: {},
        buildComplexity: {},
        buildInProgress: {},
        buildDetailOpen: null,
        codeViewerOpen: false,
        codeViewerPath: '',
        codeViewerContent: '',
        
        async init() {
            console.log('Initializing dashboard...');
            await this.loadStats();
            await this.loadSignalRadar();  // Load Layer 1 signals first
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
        
        async loadSignalRadar() {
            console.log('📡 Loading Signal Radar (Composite Signals)...');
            try {
                // Load composite signals from fast-signals endpoint
                // Server aggregates by keyword across all sources (Wikipedia, Reddit, etc.)
                const response = await fetch('/api/dashboard/fast-signals');
                
                if (response.ok) {
                    const data = await response.json();
                    
                    // Map signals - server already returns composite format
                    this.fastSignals = (data.signals || []).map(signal => ({
                        name: signal.name,
                        display_name: signal.display_name,
                        momentum: signal.momentum,
                        layer: 1,
                        source: signal.source,
                        sources: signal.sources || [{name: signal.source, momentum: signal.momentum}],
                        source_count: signal.source_count || 1,
                        agreement_score: signal.agreement_score || 100,
                        confidence: signal.confidence?.stars || 3,
                        confidence_level: signal.confidence?.agreement || 'single-source',
                        has_data: signal.has_data,
                        data_points: signal.data_points || 0,
                        has_predictions: signal.has_predictions,
                        description: signal.description
                    }));
                    
                    this.topInsight = data.top_insight || {
                        title: 'Composite Signals Active',
                        description: `Analyzing ${this.fastSignals.length} signals aggregated from multiple sources`
                    };
                    
                    console.log('📡 Composite signals loaded:', this.fastSignals.length, 
                                'multi-source:', data.multi_source_signals || 0);
                    this.filterSignals();
                } else {
                    throw new Error(`API error: ${response.status}`);
                }
            } catch (error) {
                console.error('Failed to load signals:', error);
                // Try fallback
                await this.loadFastSignalsFallback();
            }
        },
        
        async loadFastSignalsFallback() {
            try {
                // Fallback to Wikipedia-only signals
                const response = await fetch('/api/dashboard/fast-signals');
                
                if (response.ok) {
                    const data = await response.json();
                    // Map fallback signals to expected format (same as composite signals)
                    this.fastSignals = (data.signals || []).map(signal => {
                        // Strip source prefix from display_name (e.g., "Wikipedia: ChatGPT" -> "ChatGPT")
                        let cleanName = signal.display_name || signal.name;
                        if (cleanName.startsWith('Wikipedia: ')) {
                            cleanName = cleanName.replace('Wikipedia: ', '');
                        } else if (cleanName.startsWith('Reddit: ')) {
                            cleanName = cleanName.replace('Reddit: ', '');
                        }
                        
                        return {
                            name: signal.name,
                            display_name: cleanName,
                            momentum: signal.momentum,
                            layer: 1,
                            source: signal.source,
                            sources: [{name: signal.source, momentum: signal.momentum}],  // Single source
                            source_count: 1,
                            agreement_score: 100,  // Single source = 100% agreement
                            confidence: signal.confidence?.score ? Math.round(signal.confidence.score * 5) : 0,
                            confidence_level: signal.confidence?.agreement || 'single-source',
                            has_data: signal.has_data,
                            data_points: signal.data_points || 0,
                            has_predictions: signal.has_predictions,
                            description: signal.description
                        };
                    });
                    this.topInsight = data.top_insight || null;
                    console.log('📡 Fast signals loaded (single-source):', this.fastSignals.length);
                    this.filterSignals();
                } else {
                    // Ultimate fallback to placeholder
                    console.log('📡 API not ready, showing placeholder');
                    this.fastSignals = this._getPlaceholderFastSignals();
                    this.filterSignals();
                    this.topInsight = {
                        title: 'Layer 1 Setup Required',
                        description: 'Run POST /api/admin/setup-layer1-fast-signals to add Wikipedia pageview variables'
                    };
                }
            } catch (error) {
                console.error('Fallback failed:', error);
                this.fastSignals = this._getPlaceholderFastSignals();
                this.filterSignals();
            }
        },
        
        filterSignals() {
            // Apply filter based on dropdown selection
            let filtered = [...this.fastSignals];
            
            switch(this.signalFilter) {
                case 'rising':
                    filtered = filtered.filter(s => s.momentum > 0);
                    break;
                case 'falling':
                    filtered = filtered.filter(s => s.momentum < 0);
                    break;
                case 'top10':
                    filtered = filtered.slice(0, 10);
                    break;
                case 'top20':
                    filtered = filtered.slice(0, 20);
                    break;
                case 'all':
                default:
                    break;
            }
            
            this.filteredSignals = filtered;
            console.log(`📡 Filtered signals (${this.signalFilter}):`, filtered.length);
        },
        
        _getPlaceholderFastSignals() {
            // Placeholder data showing what Layer 1 will look like
            return [
                { name: 'wiki_artificial-intelligence', display_name: 'Wikipedia: AI', momentum: 15, layer: 1 },
                { name: 'wiki_bitcoin', display_name: 'Wikipedia: Bitcoin', momentum: -8, layer: 1 },
                { name: 'wiki_recession', display_name: 'Wikipedia: Recession', momentum: 22, layer: 1 },
                { name: 'wiki_layoff', display_name: 'Wikipedia: Layoff', momentum: 31, layer: 1 },
                { name: 'wiki_remote-work', display_name: 'Wikipedia: Remote Work', momentum: -5, layer: 1 }
            ];
        },
        
        async selectFastSignal(signal) {
            console.log('🎯 Selected fast signal:', signal.display_name);
            this.selectedFastSignal = signal;
            this.predictedOutcomes = [];
            this.selectedCascade = null;
            
            // Find Layer 2 variables that this signal predicts (via Granger causality)
            try {
                const response = await fetch(`/api/dashboard/cascade-predictions/${encodeURIComponent(signal.name)}`);
                
                if (response.ok) {
                    const data = await response.json();
                    
                    // Check if signal PREDICTS outcomes (normal case)
                    if (data.predictions && data.predictions.length > 0) {
                        this.predictedOutcomes = data.predictions;
                        this.selectedCascade = {
                            prediction: data.top_prediction || 'Analyzing...',
                            lag: data.optimal_lag ? `Optimal lag: ${data.optimal_lag} days` : ''
                        };
                    } 
                    // Check if signal IS PREDICTED BY something (lagging indicator)
                    else if (data.leading_indicators && data.leading_indicators.length > 0) {
                        // Show what predicts this signal (reverse direction)
                        this.predictedOutcomes = data.leading_indicators.map(li => ({
                            ...li,
                            display_name: li.display_name,
                            direction: li.direction,
                            p_value: li.p_value,
                            lag: 14,  // Default lag for display
                            is_leading: true  // Mark as leading indicator
                        }));
                        this.selectedCascade = {
                            prediction: data.top_prediction || 'Lagging indicator',
                            lag: data.note || 'This signal follows market movements'
                        };
                    }
                    // No Granger results at all
                    else {
                        this.predictedOutcomes = [];
                        this.selectedCascade = {
                            prediction: data.top_prediction || 'No empirical predictions yet',
                            lag: data.note || 'Run Granger analysis after data fetch'
                        };
                    }
                } else {
                    // API error - show message
                    this.predictedOutcomes = [];
                    this.selectedCascade = {
                        prediction: 'API error loading predictions',
                        lag: 'Try refreshing the page'
                    };
                }
            } catch (error) {
                console.error('Failed to load cascade predictions:', error);
                this.predictedOutcomes = [];
                this.selectedCascade = {
                    prediction: 'Failed to load predictions',
                    lag: error.message || 'Network error'
                };
            }
        },
        
        _getPlaceholderPredictions(signal) {
            // Show placeholder predictions based on signal type
            const predictions = [];
            
            if (signal.name.includes('ai') || signal.name.includes('intelligence')) {
                predictions.push({ 
                    name: 'NVDA', 
                    display_name: 'NVDA Stock Price', 
                    direction: signal.momentum > 0 ? 'up' : 'down',
                    p_value: '0.003',
                    lag: 21
                });
            }
            
            if (signal.name.includes('recession') || signal.name.includes('layoff')) {
                predictions.push({ 
                    name: 'unemployment', 
                    display_name: 'Unemployment Rate', 
                    direction: signal.momentum > 0 ? 'up' : 'down',
                    p_value: '0.012',
                    lag: 30
                });
            }
            
            if (signal.name.includes('bitcoin')) {
                predictions.push({ 
                    name: 'btc_price', 
                    display_name: 'BTC Price (USD)', 
                    direction: signal.momentum > 0 ? 'up' : 'down',
                    p_value: '0.008',
                    lag: 7
                });
            }
            
            // Default prediction
            if (predictions.length === 0) {
                predictions.push({ 
                    name: 'sp500', 
                    display_name: 'S&P 500 Index', 
                    direction: signal.momentum > 0 ? 'up' : 'down',
                    p_value: '0.045',
                    lag: 14
                });
            }
            
            return predictions;
        },
        
        // ============================================================
        // SIGNAL DETAIL MODAL: Open modal with source breakdown
        // ============================================================
        async openSignalModal(signal) {
            console.log('📋 Opening signal modal for:', signal.display_name);
            console.log('📋 Signal data:', JSON.stringify(signal, null, 2));
            
            // Select signal visually but DON'T auto-run Granger (set flag)
            this.selectedFastSignal = signal;
            this.predictedOutcomes = [];  // Clear - user must click Run Granger
            this.selectedCascade = {
                prediction: 'Click "Run Granger" to analyze',
                lag: ''
            };
            
            // Set basic data from the signal (already mapped in loadSignalRadar)
            this.signalModalData = {
                keyword: signal.display_name,
                momentum: signal.momentum,
                source_count: signal.source_count || 1,
                agreement_score: signal.agreement_score || 0,
                confidence: signal.confidence || 0,
                confidence_level: signal.confidence_level || '',
                sources: signal.sources || []
            };
            
            // Reset Granger + deep analysis state for modal
            this.signalGrangerResults = null;
            this.isRunningSignalGranger = false;
            this.deepAnalysis = null;
            this.isRunningDeepAnalysis = false;
            
            // Open the modal
            this.signalModalOpen = true;
            
            // Re-initialize Lucide icons for the modal
            setTimeout(() => lucide.createIcons(), 100);
            
            // Try to fetch detailed breakdown from API
            // Use signal.display_name for API lookup (e.g., "ChatGPT")
            try {
                const keyword = encodeURIComponent(signal.display_name);
                const response = await fetch(`/api/dashboard/signal-details/${keyword}`);
                
                if (response.ok) {
                    const details = await response.json();
                    console.log('📋 Signal details loaded:', details);
                    
                    // Map sources from API format (source_name) to display format (name)
                    const mappedSources = (details.sources || []).map(s => ({
                        name: s.source_name || s.name,
                        momentum: s.momentum,
                        weight_percent: s.weight_percent,
                        data_points: s.data_points
                    }));
                    
                    // Update modal data with full details
                    this.signalModalData = {
                        keyword: details.keyword || signal.display_name,
                        momentum: details.composite_momentum || signal.momentum,
                        source_count: details.source_count || signal.source_count || 1,
                        agreement_score: details.agreement_score || signal.agreement_score || 0,
                        confidence: details.confidence_stars || signal.confidence || 0,
                        confidence_level: details.confidence_level || '',
                        sources: mappedSources
                    };
                    
                    // Re-initialize icons after data update
                    setTimeout(() => lucide.createIcons(), 100);
                }
            } catch (error) {
                console.error('Failed to load signal details:', error);
                // Continue with basic data we already have
            }
        },
        
        // Calculate star rating for F-statistic (used in RHS outcome cards)
        getGrangerStars(fStat) {
            if (!fStat) return 0;
            if (fStat >= 10) return 5;
            if (fStat >= 7) return 4;
            if (fStat >= 5) return 3;
            if (fStat >= 3) return 2;
            if (fStat >= 1) return 1;
            return 0;
        },
        
        // ============================================================
        // RUN GRANGER ANALYSIS: Test FMV against ALL MVs in database
        // Results populate the RHS outcome panel
        // ============================================================
        async runSignalGranger() {
            if (!this.signalModalData.keyword) {
                console.error('No signal selected for Granger analysis');
                return;
            }
            
            console.log('🔬 Running Granger analysis for:', this.signalModalData.keyword, 'against all MVs');
            
            this.isRunningSignalGranger = true;
            this.signalGrangerResults = null;
            this.predictedOutcomes = [];  // Clear previous results
            
            try {
                // Use the cascade-predictions endpoint which tests against all MVs
                const keyword = encodeURIComponent(this.signalModalData.keyword);
                const response = await fetch(`/api/dashboard/cascade-predictions/${keyword}`);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('🔬 Granger results (all MVs):', data);
                    
                    // Populate RHS panel with predictions
                    if (data.predictions && data.predictions.length > 0) {
                        this.predictedOutcomes = data.predictions;
                        this.selectedCascade = {
                            prediction: data.top_prediction || 'Analysis complete',
                            lag: data.optimal_lag ? `Optimal lag: ${data.optimal_lag} days` : ''
                        };
                        
                        // Store summary for modal display
                        this.signalGrangerResults = {
                            total_tested: data.total_tested || data.predictions.length,
                            causal_count: data.predictions.filter(p => p.is_causal || p.p_value < 0.05).length,
                            predictions: data.predictions,
                            top_prediction: data.top_prediction,
                            stored: true,
                            timestamp: new Date().toISOString()
                        };
                        
                        // Auto-run deep analysis on top prediction
                        const topPred = data.predictions[0];
                        if (topPred && topPred.name) {
                            this.runDeepAnalysis(this.signalModalData.keyword, topPred.name);
                        }
                    } else if (data.leading_indicators && data.leading_indicators.length > 0) {
                        // This signal is predicted BY other signals (lagging indicator)
                        this.predictedOutcomes = data.leading_indicators.map(li => ({
                            ...li,
                            display_name: li.display_name,
                            direction: li.direction,
                            p_value: li.p_value,
                            lag: 14,
                            is_leading: true
                        }));
                        this.selectedCascade = {
                            prediction: data.top_prediction || 'Lagging indicator',
                            lag: data.note || 'This signal follows market movements'
                        };
                        this.signalGrangerResults = {
                            is_lagging: true,
                            leading_count: data.leading_indicators.length,
                            note: 'This signal is predicted BY other variables',
                            stored: true
                        };
                    } else {
                        // No significant Granger relationships found
                        this.predictedOutcomes = [];
                        this.selectedCascade = {
                            prediction: 'No significant predictions found',
                            lag: 'Insufficient data or no causal relationships detected'
                        };
                        this.signalGrangerResults = {
                            no_results: true,
                            note: 'No significant Granger causality detected with any market variable'
                        };
                    }
                    
                    // Re-init icons
                    setTimeout(() => lucide.createIcons(), 100);
                } else {
                    console.error('Granger API error:', response.status);
                    this.signalGrangerResults = { error: 'Failed to run analysis' };
                }
            } catch (error) {
                console.error('Failed to run Granger analysis:', error);
                this.signalGrangerResults = { error: error.message };
            } finally {
                this.isRunningSignalGranger = false;
            }
        },
        
        // ============================================================
        // DEEP ANALYSIS: Lag Curve + Regression + Prediction
        // Auto-triggered after Granger finds a causal relationship
        // ============================================================
        async runDeepAnalysis(signalKeyword, targetName) {
            console.log('📊 Running deep analysis:', signalKeyword, '→', targetName, 'momentum:', this.signalModalData.momentum);
            this.isRunningDeepAnalysis = true;
            this.deepAnalysis = null;
            
            try {
                const signal = encodeURIComponent(signalKeyword);
                const target = encodeURIComponent(targetName);
                const mom = this.signalModalData.momentum || 0;
                const response = await fetch(`/api/dashboard/deep-analysis/${signal}/${target}?momentum=${mom}`);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('📊 Deep analysis results:', data);
                    
                    if (!data.error) {
                        this.deepAnalysis = data;
                        
                        // Auto-store prediction for accuracy tracking (CA-002-10)
                        if (data.prediction) {
                            try {
                                const storeResp = await fetch('/api/dashboard/store-prediction', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify(data.prediction),
                                });
                                const storeResult = await storeResp.json();
                                console.log('🎯 Prediction stored:', storeResult.prediction_id);
                            } catch (storeErr) {
                                console.warn('Failed to store prediction:', storeErr);
                            }
                        }
                    } else {
                        console.warn('Deep analysis returned error:', data.error);
                        this.deepAnalysis = { error: data.error };
                    }
                } else {
                    console.error('Deep analysis API error:', response.status);
                    this.deepAnalysis = { error: 'API error ' + response.status };
                }
            } catch (error) {
                console.error('Deep analysis failed:', error);
                this.deepAnalysis = { error: error.message };
            } finally {
                this.isRunningDeepAnalysis = false;
                setTimeout(() => lucide.createIcons(), 100);
            }
        },
        
        // ============================================================
        // PREDICTION ACCURACY TRACKING (CA-002-10)
        // ============================================================
        
        async loadPredictions() {
            console.log('🎯 Loading Prediction Accuracy data (CA-002-10)...');
            try {
                let url = '/api/dashboard/predictions?limit=1500';
                if (this.predictionFilter) {
                    url += '&model_version=' + encodeURIComponent(this.predictionFilter);
                }
                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    console.log('🎯 Predictions loaded:', data.total, 'total');
                    
                    this.predictionServiceAvailable = true;
                    
                    // Derive service layer status from actual data
                    const hasAny = (data.total || 0) > 0;
                    const hasValidated = (data.predictions || []).some(p => p.status === 'validated');
                    this.predictionLayers = {
                        storage: hasAny,
                        updater: hasValidated || hasAny,  // updater is online if validation has been attempted
                        analytics: hasValidated
                    };
                    
                    // Populate metrics from accuracy object
                    const acc = data.accuracy || {};
                    const pendingCount = (data.predictions || []).filter(p => p.status === 'pending').length;
                    const validatedCount = (data.predictions || []).filter(p => p.status === 'validated').length;
                    this.predictionMetrics = {
                        total_predictions: data.total || 0,
                        pending: pendingCount,
                        validated: validatedCount,
                        pair_count: data.pair_count || 0,
                        direction_accuracy: acc.direction_accuracy != null ? acc.direction_accuracy : null,
                        avg_error_pct: acc.avg_error_pct != null ? acc.avg_error_pct : null,
                        avg_lag_error_days: acc.avg_lag_error_days != null ? acc.avg_lag_error_days : null,
                        avg_change_error_pct: acc.avg_change_error_pct != null ? acc.avg_change_error_pct : null
                    };
                    
                    // Store time series for charts
                    this.timeSeriesData = data.time_series || [];
                    
                    // Build full timeseries for charts
                    if (data.predictions && data.predictions.length > 0) {
                        this.predictionTimeseries = data.predictions.map(p => ({
                            target_date: p.target_date,
                            predicted_at: p.predicted_at,
                            predicted_value: p.predicted_value,
                            actual_value: p.actual_value,
                            predicted_change_pct: p.predicted_change_pct,
                            actual_change_pct: p.actual_change_pct,
                            optimal_lag_days: p.optimal_lag_days,
                            actual_lag_days: p.actual_lag_days,
                            lag_error_days: p.lag_error_days,
                            predicted_direction: p.predicted_direction,
                            direction_correct: p.direction_correct,
                            signal_name: p.signal_name,
                            target_name: p.target_name,
                            target_source: p.target_source,
                            status: p.status,
                            r_squared: p.r_squared,
                            granger_p_value: p.granger_p_value,
                            confidence: p.confidence
                        }));
                    }
                    
                    // Render time series charts
                    this.$nextTick(() => {
                        this.renderPredictionCharts();
                    });
                    
                    // Store raw predictions for the table
                    this.recentPredictions = data.predictions || [];
                } else {
                    this.predictionServiceAvailable = false;
                }
            } catch (error) {
                console.error('Prediction load failed:', error);
                this.predictionServiceAvailable = false;
            }
            setTimeout(() => lucide.createIcons(), 100);
        },
        
        renderPredictionCharts() {
            if (typeof Plotly === 'undefined' || this.timeSeriesData.length === 0) return;
            
            const ts = this.timeSeriesData;
            const months = ts.map(t => t.month);
            
            const chartLayout = (yTitle) => ({
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: { color: '#94a3b8', size: 11 },
                margin: { t: 10, r: 20, b: 40, l: 60 },
                xaxis: { gridcolor: '#1e293b', tickfont: { size: 10 }, tickangle: -45 },
                yaxis: { title: yTitle, gridcolor: '#1e293b', tickfont: { size: 10 }, titlefont: { size: 11 } },
                legend: { orientation: 'h', y: 1.12, font: { size: 11 } },
                showlegend: true,
                hovermode: 'x unified'
            });
            const chartConfig = { responsive: true, displayModeBar: false };
            
            // Chart 1: Change % — Predicted vs Actual
            const el1 = document.getElementById('chartChangePct');
            if (el1) {
                const predChange = ts.map(t => t.avg_predicted_change_pct);
                const actChange = ts.map(t => t.avg_actual_change_pct);
                Plotly.newPlot(el1, [
                    {
                        x: months, y: predChange, name: 'Predicted Change %',
                        type: 'scatter', mode: 'lines+markers',
                        line: { color: '#6366f1', width: 2.5 },
                        marker: { size: 6 }
                    },
                    {
                        x: months, y: actChange, name: 'Actual Change %',
                        type: 'scatter', mode: 'lines+markers',
                        line: { color: '#22c55e', width: 2.5 },
                        marker: { size: 6 }
                    }
                ], chartLayout('Change %'), chartConfig);
            }
            
            // Chart 2: Lag — Predicted vs Actual
            const el2 = document.getElementById('chartLag');
            if (el2) {
                const predLag = ts.map(t => t.avg_predicted_lag);
                const actLag = ts.map(t => t.avg_actual_lag);
                Plotly.newPlot(el2, [
                    {
                        x: months, y: predLag, name: 'Predicted Lag (days)',
                        type: 'scatter', mode: 'lines+markers',
                        line: { color: '#6366f1', width: 2.5 },
                        marker: { size: 6 }
                    },
                    {
                        x: months, y: actLag, name: 'Actual Lag (days)',
                        type: 'scatter', mode: 'lines+markers',
                        line: { color: '#22c55e', width: 2.5 },
                        marker: { size: 6 }
                    }
                ], chartLayout('Days'), chartConfig);
            }
            
            // Chart 3: Direction Accuracy Over Time
            const el3 = document.getElementById('chartDirectionAcc');
            if (el3) {
                const dirAcc = ts.map(t => t.direction_accuracy);
                const counts = ts.map(t => t.count);
                Plotly.newPlot(el3, [
                    {
                        x: months, y: dirAcc, name: 'Direction Accuracy',
                        type: 'scatter', mode: 'lines+markers',
                        line: { color: '#f59e0b', width: 2.5 },
                        marker: { size: 6 },
                        text: counts.map(c => c + ' predictions'),
                        hovertemplate: '%{y:.1f}% (%{text})<extra></extra>'
                    },
                    {
                        x: [months[0], months[months.length - 1]],
                        y: [50, 50],
                        name: 'Random Baseline (50%)',
                        type: 'scatter', mode: 'lines',
                        line: { color: '#475569', width: 1.5, dash: 'dash' }
                    },
                    {
                        x: [months[0], months[months.length - 1]],
                        y: [90, 90],
                        name: 'M0 Target (90%)',
                        type: 'scatter', mode: 'lines',
                        line: { color: '#ef4444', width: 1.5, dash: 'dot' }
                    }
                ], {
                    ...chartLayout('Accuracy %'),
                    yaxis: { ...chartLayout('Accuracy %').yaxis, range: [0, 100] }
                }, chartConfig);
            }
        },
        
        async triggerActualUpdate() {
            this.isUpdatingActuals = true;
            try {
                const response = await fetch('/api/dashboard/predictions/validate', { method: 'POST' });
                if (response.ok) {
                    const data = await response.json();
                    console.log('🎯 Validation result:', data);
                    if (data.validated > 0) {
                        console.log(`✅ Validated ${data.validated} predictions. Direction accuracy: ${data.accuracy_stats?.direction_accuracy}%`);
                    }
                }
                // Reload all predictions data after validating
                await this.loadPredictions();
            } catch (error) {
                console.error('Prediction validation failed:', error);
            } finally {
                this.isUpdatingActuals = false;
            }
        },

        // ============================================================
        // EXPLOITATION BOARD METHODS
        // ============================================================
        async loadExploitationRecommendations() {
            try {
                const params = new URLSearchParams();
                if (this.exploitationFilterAction) params.set('action_type', this.exploitationFilterAction);
                if (this.exploitationFilterStatus) params.set('status', this.exploitationFilterStatus);
                const url = '/api/dashboard/exploitation/recommendations' + (params.toString() ? '?' + params : '');
                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    this.exploitationRecommendations = data.recommendations || [];
                    this.filteredExploitation = this.exploitationRecommendations;
                    const summary = data.summary || {};
                    this.exploitationStats = {
                        total: data.total || 0,
                        by_action_type: summary.by_action_type || {},
                        by_status: summary.by_status || {},
                        avg_score: summary.average_score || 0
                    };
                    console.log(`📊 Loaded ${this.exploitationRecommendations.length} exploitation recommendations`);
                    // Load build statuses for BUILD cards
                    await this.loadBuilds();
                }
            } catch (error) {
                console.error('Failed to load exploitation recommendations:', error);
            }
        },

        async generateRecommendations() {
            this.isGeneratingRecommendations = true;
            try {
                const response = await fetch('/api/dashboard/exploitation/generate');
                if (response.ok) {
                    const data = await response.json();
                    console.log('🚀 Generated recommendations:', data);
                    // Reload the recommendations list
                    await this.loadExploitationRecommendations();
                } else {
                    const err = await response.json();
                    console.error('Generation failed:', err);
                }
            } catch (error) {
                console.error('Failed to generate recommendations:', error);
            } finally {
                this.isGeneratingRecommendations = false;
            }
        },

        filterExploitation() {
            this.filteredExploitation = this.exploitationRecommendations.filter(rec => {
                if (this.exploitationFilterAction && rec.action_type !== this.exploitationFilterAction) return false;
                if (this.exploitationFilterStatus && rec.status !== this.exploitationFilterStatus) return false;
                return true;
            });
        },

        async updateRecommendationStatus(id, newStatus) {
            try {
                const response = await fetch(`/api/dashboard/exploitation/recommendations/${id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
                if (response.ok) {
                    // Update local state
                    const rec = this.exploitationRecommendations.find(r => r.id === id);
                    if (rec) rec.status = newStatus;
                    console.log(`✅ Updated recommendation ${id} to ${newStatus}`);
                }
            } catch (error) {
                console.error('Failed to update recommendation status:', error);
            }
        },

        async updateRecommendationNotes(id, notes) {
            try {
                const response = await fetch(`/api/dashboard/exploitation/recommendations/${id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notes: notes })
                });
                if (response.ok) {
                    // Update local state
                    const rec = this.exploitationRecommendations.find(r => r.id === id);
                    if (rec) rec.notes = notes;
                }
            } catch (error) {
                console.error('Failed to update recommendation notes:', error);
            }
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
                alert(`✅ All correlations have been refreshed! Your scatter plots now show the complete data.`);
                
                // Refresh dashboard after recalculation
                await this.refreshAll();
                
            } catch (error) {
                console.error('Recalculation failed:', error);
                alert('⚠️ Couldn\'t refresh correlations. Please try again or contact support if this persists.');
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
                
                // Try to extract meaningful error message
                let errorMessage = '⚠️ Unable to test causality';
                let errorDetails = '';
                
                // Extract error detail from Error message (fetch API pattern)
                const errorText = error.message || error.toString();
                
                if (errorText.includes('Insufficient data')) {
                    // Extract the specific numbers
                    const match = errorText.match(/(\d+) observations.*need (\d+)/);
                    if (match) {
                        const [_, current, needed] = match;
                        errorMessage = '📊 Not enough data yet';
                        errorDetails = `\n\nThis pair has ${current} data points but needs ${needed} for reliable analysis.\n\nAs you collect more data over time, statistical power will increase and causality testing will become possible.\n\nTip: Daily data pairs work best with 100+ points, quarterly data needs 20+ points.`;
                    } else {
                        errorMessage = '📊 Not enough data yet';
                        errorDetails = '\n\nThese variables don\'t have enough overlapping observations for reliable causality testing. Keep collecting data and try again later!';
                    }
                } else if (errorText.includes('frequency')) {
                    errorMessage = '📈 Data frequency mismatch';
                    errorDetails = '\n\nThese variables have different data frequencies (e.g., daily vs quarterly). The system will downsample to match, but needs more observations at the lower frequency.';
                } else {
                    errorMessage = '⚠️ Causality test error';
                    errorDetails = `\n\n${errorText}`;
                }
                
                alert(errorMessage + errorDetails);
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
        },

        // ============================================================
        // PROGRAMME BASELINES (M0)
        // ============================================================

        async loadBaselines() {
            this.baselinesLoading = true;
            try {
                const response = await fetch('/api/dashboard/baselines');
                if (response.ok) {
                    this.baselines = await response.json();
                    console.log('📊 Baselines loaded:', this.baselines);
                    this.$nextTick(() => this.renderBaselineSparklines());
                } else {
                    console.error('Failed to load baselines:', response.status);
                    this.baselines = null;
                }
            } catch (e) {
                console.error('Baselines fetch error:', e);
                this.baselines = null;
            }
            this.baselinesLoading = false;
        },

        // ============================================================
        // REVENUE DASHBOARD (M1 Track E)
        // ============================================================

        async loadRevenue() {
            this.revenueLoading = true;
            try {
                const response = await fetch('/revenue/dashboard');
                if (response.ok) {
                    this.revenueData = await response.json();
                    console.log('💰 Revenue loaded:', this.revenueData);
                    this.$nextTick(() => this.renderRevenueChart());
                } else {
                    console.error('Failed to load revenue:', response.status);
                    this.revenueData = null;
                }
            } catch (e) {
                console.error('Revenue fetch error:', e);
                this.revenueData = null;
            }
            this.revenueLoading = false;
        },

        renderRevenueChart() {
            const history = this.revenueData?.mrr_history || [];
            if (history.length === 0) return;

            const el = document.getElementById('revenue-mrr-chart');
            if (!el) return;

            Plotly.newPlot(el, [{
                x: history.map(h => h.month),
                y: history.map(h => h.mrr),
                type: 'bar',
                marker: { color: '#22c55e', opacity: 0.8 },
                hovertemplate: '%{x}<br>$%{y:.2f}<extra></extra>',
            }], {
                margin: { t: 10, r: 20, b: 40, l: 60 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { color: '#94a3b8', gridcolor: '#334155' },
                yaxis: { color: '#94a3b8', gridcolor: '#334155', tickprefix: '$' },
                font: { color: '#94a3b8' },
            }, { responsive: true, displayModeBar: false });
        },

        renderBaselineSparklines() {
            const darkLayout = {
                margin: { t: 2, r: 4, b: 2, l: 4 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { visible: false },
                yaxis: { visible: false },
                showlegend: false,
            };
            const config = { responsive: true, displayModeBar: false };

            // Model accuracy sparkline
            const modelTrend = this.baselines?.model_accuracy?.trend || [];
            if (modelTrend.length > 0) {
                Plotly.newPlot('baseline-model-sparkline', [{
                    x: modelTrend.map(t => t.month),
                    y: modelTrend.map(t => t.accuracy),
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#3b82f6', width: 2 },
                    marker: { size: 4 },
                }], { ...darkLayout, yaxis: { visible: false, range: [0, 100] } }, config);
            }


        },

        // Exploitation Validation Modal
        openValidationModal(recId, recName) {
            this.validationRecId = recId;
            this.validationRecName = recName;
            this.validationForm = {
                actual_outcome: 'UNKNOWN',
                outcome_notes: '',
                demand_accurate: null,
                competition_accurate: null,
                revenue_potential_accurate: null,
                actual_revenue: null,
            };
            this.validationModalOpen = true;
        },

        async submitValidation() {
            try {
                const payload = {
                    recommendation_id: this.validationRecId,
                    ...this.validationForm,
                };
                const response = await fetch('/api/dashboard/exploitation/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (response.ok) {
                    console.log('✅ Validation saved');
                    this.validationModalOpen = false;
                    // Refresh exploitation list
                    await this.loadExploitationRecommendations();
                } else {
                    console.error('Validation save failed:', response.status);
                }
            } catch (e) {
                console.error('Validation error:', e);
            }
        },

        // ============================================================
        // MVP Build
        // ============================================================
        async startBuild(recId) {
            console.log('🔨 startBuild called for rec', recId);
            const complexity = this.buildComplexity[recId] || 'LOW';
            this.buildInProgress = {...this.buildInProgress, [recId]: true};
            try {
                const res = await fetch('/api/dashboard/exploitation/build', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ recommendation_id: recId, complexity }),
                });
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}));
                    console.error('Build start failed:', err.detail || res.status);
                    this.buildInProgress = {...this.buildInProgress, [recId]: false};
                    return;
                }
                const data = await res.json();
                console.log('🔨 Build started:', data.build_id);
                this.builds = {...this.builds, [recId]: { status: data.status, build_id: data.build_id }};
                this.pollBuildStatus(recId, data.build_id);
            } catch (e) {
                console.error('Build error:', e);
                this.buildInProgress = {...this.buildInProgress, [recId]: false};
            }
        },

        async pollBuildStatus(recId, buildId) {
            const gen = this._buildPollGen = (this._buildPollGen || 0) + 1;
            const poll = async () => {
                if (this._buildPollGen !== gen) return; // loadBuilds() ran — stop stale poll
                try {
                    const res = await fetch(`/api/dashboard/exploitation/builds/${buildId}`);
                    if (!res.ok) return;
                    const data = await res.json();
                    if (this._buildPollGen !== gen) return;
                    this.builds = {...this.builds, [recId]: data};
                    if (['QUEUED', 'GENERATING', 'UPLOADING', 'DEPLOYING'].includes(data.status)) {
                        setTimeout(poll, 3000);
                    } else {
                        this.buildInProgress = {...this.buildInProgress, [recId]: false};
                    }
                    this.$nextTick(() => { try { lucide.createIcons(); } catch(e) {} });
                } catch (e) {
                    console.error('Poll error:', e);
                    this.buildInProgress = {...this.buildInProgress, [recId]: false};
                }
            };
            setTimeout(poll, 2000);
        },

        async loadBuilds() {
            this._buildPollGen = (this._buildPollGen || 0) + 1; // cancel stale polls
            try {
                const res = await fetch('/api/dashboard/exploitation/builds');
                if (!res.ok) return;
                const data = await res.json();
                const updated = {...this.builds};
                const terminal = new Set(['LIVE', 'FAILED']);
                for (const b of (data.builds || [])) {
                    const existing = updated[b.recommendation_id];
                    // Prefer terminal (LIVE/FAILED) over in-progress builds
                    if (existing && terminal.has(existing.status) && !terminal.has(b.status)) continue;
                    updated[b.recommendation_id] = b;
                }
                this.builds = updated;
            } catch (e) {
                console.error('Load builds error:', e);
            }
        },

        async viewBuildFile(buildId, fileId, filePath) {
            this.codeViewerPath = filePath;
            this.codeViewerContent = 'Loading...';
            this.codeViewerOpen = true;
            try {
                const res = await fetch(`/api/dashboard/exploitation/builds/${buildId}/files/${fileId}`);
                if (!res.ok) {
                    this.codeViewerContent = 'Failed to load file content';
                    return;
                }
                const data = await res.json();
                this.codeViewerContent = data.content || '(empty file)';
            } catch (e) {
                this.codeViewerContent = 'Error: ' + e.message;
            }
        }
    };
}
