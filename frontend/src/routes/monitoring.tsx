/**
 * Monitoring page - Real-time monitoring and metrics
 */

import { createFileRoute } from '@tanstack/react-router';
import { useAtom } from 'jotai';
import { 
  servicesAtom, 
  taskHistoryAtom,
  connectionStatusAtom,
  notificationsAtom
} from '../stores/atoms';
import { useServices, useHealth } from '../hooks/useApi';
import { 
  Activity, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Bell,
  BarChart3,
  Clock,
  Zap
} from 'lucide-react';

function MonitoringPage() {
  const [services] = useAtom(servicesAtom);
  const [taskHistory] = useAtom(taskHistoryAtom);
  const [connectionStatus] = useAtom(connectionStatusAtom);
  const [notifications] = useAtom(notificationsAtom);

  const { data: healthData } = useHealth();
  const { isLoading: servicesLoading } = useServices();

  // Calculate metrics
  const totalRequests = services.reduce((sum, service) => sum + service.metrics.total_requests, 0);
  const totalSuccessful = services.reduce((sum, service) => sum + service.metrics.successful_requests, 0);
  const totalFailed = services.reduce((sum, service) => sum + service.metrics.failed_requests, 0);
  const avgResponseTime = services.length > 0 
    ? services.reduce((sum, service) => sum + service.metrics.average_response_time, 0) / services.length 
    : 0;
  const healthyServices = services.filter(service => service.health).length;

  // Task metrics
  const completedTasks = taskHistory.filter(task => task.status === 'completed').length;
  const failedTasks = taskHistory.filter(task => task.status === 'failed').length;
  const taskSuccessRate = taskHistory.length > 0 ? (completedTasks / taskHistory.length) * 100 : 0;

  // Recent activity (last 24 hours)
  const now = new Date();
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const recentTasks = taskHistory.filter(task => new Date(task.created_at) > yesterday);
  const recentNotifications = notifications.slice(0, 5);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'text-green-600';
      case 'connecting':
        return 'text-yellow-600';
      case 'disconnected':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Bell className="w-4 h-4 text-blue-500" />;
    }
  };

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Monitoring</h1>
        <p className="mt-2 text-gray-600">
          Real-time system monitoring and performance metrics
        </p>
      </div>

      {/* System Status */}
      <div className="mb-8 bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">System Status</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-center space-x-3">
            <div className={`w-4 h-4 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-500' : 
              connectionStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
            }`} />
            <div>
              <div className="text-sm font-medium text-gray-900">Connection Status</div>
              <div className={`text-sm ${getStatusColor(connectionStatus)}`}>
                {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {healthData?.data?.status === 'healthy' ? (
              <CheckCircle className="w-4 h-4 text-green-500" />
            ) : (
              <XCircle className="w-4 h-4 text-red-500" />
            )}
            <div>
              <div className="text-sm font-medium text-gray-900">API Health</div>
              <div className={`text-sm ${
                healthData?.data?.status === 'healthy' ? 'text-green-600' : 'text-red-600'
              }`}>
                {healthData?.data?.status || 'Unknown'}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {healthyServices === services.length ? (
              <CheckCircle className="w-4 h-4 text-green-500" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-yellow-500" />
            )}
            <div>
              <div className="text-sm font-medium text-gray-900">Services Health</div>
              <div className="text-sm text-gray-600">
                {healthyServices}/{services.length} healthy
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BarChart3 className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Requests
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {servicesLoading ? '...' : totalRequests.toLocaleString()}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Success Rate
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {totalRequests > 0 ? ((totalSuccessful / totalRequests) * 100).toFixed(1) : '0'}%
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Clock className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Avg Response Time
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {avgResponseTime.toFixed(2)}s
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Zap className="h-8 w-8 text-orange-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Tasks Today
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {recentTasks.length}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Service Performance */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Service Performance</h3>
          </div>
          <div className="p-6">
            {servicesLoading ? (
              <div className="text-center text-gray-500">Loading services...</div>
            ) : services.length === 0 ? (
              <div className="text-center text-gray-500">No services available</div>
            ) : (
              <div className="space-y-4">
                {services.map((service) => (
                  <div key={service.name} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {service.health ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-500" />
                        )}
                        <span className="font-medium text-gray-900">{service.name}</span>
                      </div>
                      <span className="text-sm text-gray-500">
                        {service.metrics.success_rate.toFixed(1)}% success
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="text-gray-500">Requests</div>
                        <div className="font-medium">{service.metrics.total_requests}</div>
                      </div>
                      <div>
                        <div className="text-gray-500">Avg Time</div>
                        <div className="font-medium">{service.metrics.average_response_time.toFixed(2)}s</div>
                      </div>
                      <div>
                        <div className="text-gray-500">Errors</div>
                        <div className="font-medium text-red-600">{service.metrics.failed_requests}</div>
                      </div>
                    </div>

                    {/* Performance Bar */}
                    <div className="mt-3">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            service.metrics.success_rate >= 95 ? 'bg-green-500' :
                            service.metrics.success_rate >= 80 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${Math.min(service.metrics.success_rate, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          </div>
          <div className="p-6">
            {/* Recent Notifications */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Notifications</h4>
              {recentNotifications.length === 0 ? (
                <div className="text-sm text-gray-500">No recent notifications</div>
              ) : (
                <div className="space-y-2">
                  {recentNotifications.map((notification) => (
                    <div key={notification.id} className="flex items-start space-x-2 p-2 bg-gray-50 rounded">
                      {getNotificationIcon(notification.type)}
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-gray-900">{notification.message}</div>
                        <div className="text-xs text-gray-500">
                          {notification.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Task Summary */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">Task Summary (24h)</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{completedTasks}</div>
                  <div className="text-sm text-green-700">Completed</div>
                </div>
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">{failedTasks}</div>
                  <div className="text-sm text-red-700">Failed</div>
                </div>
              </div>
              
              {taskHistory.length > 0 && (
                <div className="mt-4 text-center">
                  <div className="text-sm text-gray-500">Task Success Rate</div>
                  <div className="text-xl font-bold text-gray-900">
                    {taskSuccessRate.toFixed(1)}%
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Performance Trends */}
      {services.length > 0 && (
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Overview</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <Activity className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <div className="text-sm text-gray-500">System Load</div>
              <div className="text-lg font-semibold text-gray-900">
                {services.filter(s => s.status === 'running').length}/{services.length} active
              </div>
            </div>
            
            <div className="text-center">
              <TrendingUp className="w-8 h-8 text-green-600 mx-auto mb-2" />
              <div className="text-sm text-gray-500">Overall Health</div>
              <div className="text-lg font-semibold text-gray-900">
                {((healthyServices / services.length) * 100).toFixed(0)}%
              </div>
            </div>
            
            <div className="text-center">
              <Clock className="w-8 h-8 text-purple-600 mx-auto mb-2" />
              <div className="text-sm text-gray-500">Uptime</div>
              <div className="text-lg font-semibold text-gray-900">
                {services.length > 0 ? 
                  Math.max(...services.map(s => s.metrics.uptime_seconds / 3600)).toFixed(1) + 'h' 
                  : '0h'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export const Route = createFileRoute('/monitoring')({
  component: MonitoringPage,
});