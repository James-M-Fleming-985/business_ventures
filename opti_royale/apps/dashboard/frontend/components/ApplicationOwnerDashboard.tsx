import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  Users, 
  DollarSign, 
  Target, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  Database,
  Cpu,
  Monitor
} from 'lucide-react';

interface DashboardData {
  systemHealth: {
    status: string;
    uptime: string;
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    api_response_time: number;
    api_error_rate: number;
    api_throughput: number;
  };
  businessMetrics: {
    mrr: number;
    growth_rate: number;
    total_users: number;
    active_users_daily: number;
    active_users_weekly: number;
    active_users_monthly: number;
    new_signups_today: number;
    churn_rate: number;
    nps_score: number;
  };
  aiPerformance: {
    analysis_accuracy: number;
    mechanics_coverage: number;
    video_recognition_accuracy: number;
    avg_processing_time: number;
    confidence_score: number;
    queue_length: number;
  };
  alerts: Array<{
    id: string;
    severity: string;
    component: string;
    message: string;
    timestamp: string;
    acknowledged: boolean;
    resolved: boolean;
  }>;
  timestamp: string;
}

const ApplicationOwnerDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await fetch('/api/dashboard/summary');
        if (!response.ok) {
          throw new Error('Failed to fetch dashboard data');
        }
        const data = await response.json();
        setDashboardData(data);
        setLastUpdate(new Date());
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchDashboardData();

    // Set up WebSocket for real-time updates
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/dashboard`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setDashboardData(data);
        setLastUpdate(new Date());
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Real-time connection lost');
    };

    // Cleanup
    return () => {
      ws.close();
    };
  }, []);

  const getStatusIcon = (status: string) => {
    if (status.includes('🟢') || status.includes('Healthy')) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else if (status.includes('🟡') || status.includes('Warning')) {
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    } else {
      return <XCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const colors = {
      CRITICAL: 'bg-red-500 text-white',
      WARNING: 'bg-yellow-500 text-black',
      INFO: 'bg-blue-500 text-white'
    };
    return (
      <Badge className={colors[severity as keyof typeof colors] || 'bg-gray-500 text-white'}>
        {severity}
      </Badge>
    );
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <Alert className="m-4">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          {error || 'Failed to load dashboard data'}
        </AlertDescription>
      </Alert>
    );
  }

  const { systemHealth, businessMetrics, aiPerformance, alerts } = dashboardData;

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">OptiRoyale Dashboard</h1>
          <p className="text-gray-600">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon(systemHealth.status)}
          <span className="text-lg font-medium">{systemHealth.status}</span>
        </div>
      </div>

      {/* Executive Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemHealth.status.includes('🟢') ? '99.9%' : '95.2%'}
            </div>
            <p className="text-xs text-muted-foreground">
              Uptime: {systemHealth.uptime}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(businessMetrics.mrr)}</div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline w-3 h-3" /> +{businessMetrics.growth_rate.toFixed(1)}% MoM
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatNumber(businessMetrics.active_users_daily)}
            </div>
            <p className="text-xs text-muted-foreground">
              Daily active users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Accuracy</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {aiPerformance.analysis_accuracy.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Analysis accuracy
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="system">System Health</TabsTrigger>
          <TabsTrigger value="business">Business</TabsTrigger>
          <TabsTrigger value="ai">AI Performance</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* System Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Monitor className="w-5 h-5 mr-2" />
                  System Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>API Response Time</span>
                  <Badge variant="outline">{systemHealth.api_response_time.toFixed(2)}s</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Error Rate</span>
                  <Badge variant="outline">{systemHealth.api_error_rate.toFixed(2)}%</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Throughput</span>
                  <Badge variant="outline">{systemHealth.api_throughput} req/min</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Queue Length</span>
                  <Badge variant="outline">{aiPerformance.queue_length}</Badge>
                </div>
              </CardContent>
            </Card>

            {/* Business Metrics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Key Business Metrics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Total Users</span>
                  <Badge variant="outline">{formatNumber(businessMetrics.total_users)}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>New Signups Today</span>
                  <Badge variant="outline">+{businessMetrics.new_signups_today}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Churn Rate</span>
                  <Badge variant="outline">{businessMetrics.churn_rate.toFixed(1)}%</Badge>
                </div>
                <div className="flex justify-between">
                  <span>NPS Score</span>
                  <Badge variant="outline">{businessMetrics.nps_score.toFixed(1)}/10</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Cpu className="w-5 h-5 mr-2" />
                  CPU Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{systemHealth.cpu_usage.toFixed(1)}%</div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${systemHealth.cpu_usage}%` }}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Database className="w-5 h-5 mr-2" />
                  Memory Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{systemHealth.memory_usage.toFixed(1)}%</div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full" 
                    style={{ width: `${systemHealth.memory_usage}%` }}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Clock className="w-5 h-5 mr-2" />
                  Disk Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{systemHealth.disk_usage.toFixed(1)}%</div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-purple-600 h-2 rounded-full" 
                    style={{ width: `${systemHealth.disk_usage}%` }}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="business" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>User Engagement</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Daily Active Users</span>
                  <Badge>{formatNumber(businessMetrics.active_users_daily)}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Weekly Active Users</span>
                  <Badge>{formatNumber(businessMetrics.active_users_weekly)}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Monthly Active Users</span>
                  <Badge>{formatNumber(businessMetrics.active_users_monthly)}</Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Revenue Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Monthly Recurring Revenue</span>
                  <Badge>{formatCurrency(businessMetrics.mrr)}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Growth Rate</span>
                  <Badge>+{businessMetrics.growth_rate.toFixed(1)}%</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Churn Rate</span>
                  <Badge>{businessMetrics.churn_rate.toFixed(1)}%</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="ai" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Analysis Accuracy</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{aiPerformance.analysis_accuracy.toFixed(1)}%</div>
                <p className="text-sm text-muted-foreground">Overall accuracy</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Mechanics Coverage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{aiPerformance.mechanics_coverage.toFixed(1)}%</div>
                <p className="text-sm text-muted-foreground">Database coverage</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Processing Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{aiPerformance.avg_processing_time.toFixed(1)}s</div>
                <p className="text-sm text-muted-foreground">Average processing</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <div className="space-y-4">
            {alerts.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center text-muted-foreground">
                    <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
                    <p>No active alerts</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              alerts.map((alert) => (
                <Alert key={alert.id}>
                  <AlertTriangle className="h-4 w-4" />
                  <div className="flex justify-between items-start">
                    <div>
                      <AlertDescription>
                        <div className="flex items-center space-x-2 mb-1">
                          {getSeverityBadge(alert.severity)}
                          <Badge variant="outline">{alert.component}</Badge>
                        </div>
                        <p>{alert.message}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {new Date(alert.timestamp).toLocaleString()}
                        </p>
                      </AlertDescription>
                    </div>
                  </div>
                </Alert>
              ))
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ApplicationOwnerDashboard;
