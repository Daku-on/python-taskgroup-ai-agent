/**
 * Dashboard page - Main overview
 */

import { createFileRoute } from '@tanstack/react-router';
import { useAtom } from 'jotai';
import { 
  servicesAtom, 
  healthyServicesCountAtom, 
  totalRequestsAtom,
  taskHistoryAtom,
  connectionStatusAtom 
} from '../stores/atoms';
import { useServices, useHealth } from '../hooks/useApi';
import { Activity, CheckCircle, XCircle, Clock, Server, Zap, Calendar, ArrowRight } from 'lucide-react';
import { Link } from '@tanstack/react-router';

function DashboardPage() {
  const [services] = useAtom(servicesAtom);
  const [healthyCount] = useAtom(healthyServicesCountAtom);
  const [totalRequests] = useAtom(totalRequestsAtom);
  const [taskHistory] = useAtom(taskHistoryAtom);
  const [connectionStatus] = useAtom(connectionStatusAtom);

  // API hooks
  const { data: healthData, isLoading: healthLoading } = useHealth();
  const { isLoading: servicesLoading, error: servicesError } = useServices();

  // Calculate statistics
  const recentTasks = taskHistory.slice(0, 5);
  const successfulTasks = taskHistory.filter(task => task.status === 'completed').length;
  const successRate = taskHistory.length > 0 ? (successfulTasks / taskHistory.length) * 100 : 0;

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Python TaskGroup AI Agent システムの監視とコントロール
        </p>
      </div>

      {/* Connection Status */}
      <div className="mb-6">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500' : 
            connectionStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
          }`} />
          <span className="text-sm text-gray-600">
            {connectionStatus === 'connected' ? 'Connected' : 
             connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Total Services */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Server className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Services
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {servicesLoading ? '...' : services.length}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        {/* Healthy Services */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Healthy Services
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {servicesLoading ? '...' : `${healthyCount}/${services.length}`}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        {/* Total Requests */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Zap className="h-8 w-8 text-purple-600" />
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

        {/* Success Rate */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Activity className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Success Rate
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {successRate.toFixed(1)}%
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link 
            to="/interviews"
            className="block bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white hover:from-blue-600 hover:to-blue-700 transition-all duration-200 transform hover:scale-105"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center mb-2">
                  <Calendar className="w-6 h-6 mr-2" />
                  <h3 className="text-lg font-semibold">Interview Scheduling</h3>
                </div>
                <p className="text-blue-100 text-sm">
                  Complete automated interview scheduling with Google integration
                </p>
              </div>
              <ArrowRight className="w-5 h-5" />
            </div>
          </Link>
          
          <Link 
            to="/tasks"
            className="block bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white hover:from-purple-600 hover:to-purple-700 transition-all duration-200 transform hover:scale-105"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center mb-2">
                  <Activity className="w-6 h-6 mr-2" />
                  <h3 className="text-lg font-semibold">Task Management</h3>
                </div>
                <p className="text-purple-100 text-sm">
                  Execute and monitor AI agent tasks
                </p>
              </div>
              <ArrowRight className="w-5 h-5" />
            </div>
          </Link>
          
          <Link 
            to="/services"
            className="block bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white hover:from-green-600 hover:to-green-700 transition-all duration-200 transform hover:scale-105"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center mb-2">
                  <Server className="w-6 h-6 mr-2" />
                  <h3 className="text-lg font-semibold">Service Control</h3>
                </div>
                <p className="text-green-100 text-sm">
                  Manage and monitor system services
                </p>
              </div>
              <ArrowRight className="w-5 h-5" />
            </div>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Services Status */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Services Status</h3>
          </div>
          <div className="p-6">
            {servicesLoading ? (
              <div className="text-center text-gray-500">Loading services...</div>
            ) : servicesError ? (
              <div className="text-center text-red-500">
                Error loading services: {servicesError instanceof Error ? servicesError.message : String(servicesError)}
              </div>
            ) : services.length === 0 ? (
              <div className="text-center text-gray-500">No services available</div>
            ) : (
              <div className="space-y-4">
                {services.map((service) => (
                  <div key={service.name} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full mr-3 ${
                        service.health ? 'bg-green-500' : 'bg-red-500'
                      }`} />
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {service.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {service.status}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {service.metrics.total_requests} requests
                      </div>
                      <div className="text-sm text-gray-500">
                        {service.metrics.success_rate.toFixed(1)}% success
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Tasks */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Tasks</h3>
          </div>
          <div className="p-6">
            {recentTasks.length === 0 ? (
              <div className="text-center text-gray-500">No recent tasks</div>
            ) : (
              <div className="space-y-4">
                {recentTasks.map((task) => (
                  <div key={task.task_id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      {task.status === 'completed' ? (
                        <CheckCircle className="w-4 h-4 text-green-500 mr-3" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500 mr-3" />
                      )}
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {task.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(task.created_at).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      {task.status}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="mt-8 bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">System Health</h3>
        <div className="flex items-center">
          {healthLoading ? (
            <Clock className="w-5 h-5 text-yellow-500 mr-2" />
          ) : healthData?.data?.status === 'healthy' ? (
            <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
          ) : (
            <XCircle className="w-5 h-5 text-red-500 mr-2" />
          )}
          <span className="text-sm text-gray-600">
            {healthLoading ? 'Checking system health...' :
             healthData?.data?.status === 'healthy' ? 'All systems operational' :
             'System health check failed'}
          </span>
        </div>
      </div>
    </div>
  );
}

export const Route = createFileRoute('/')({
  component: DashboardPage,
});