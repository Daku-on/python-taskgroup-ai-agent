/**
 * Services page - Service management and monitoring
 */

import { createFileRoute } from '@tanstack/react-router';
import { useAtom } from 'jotai';
import { 
  servicesAtom, 
  filteredServicesAtom,
  serviceFilterAtom,
  servicesLoadingAtom,
  servicesErrorAtom
} from '../stores/atoms';
import { useServices } from '../hooks/useApi';
import { 
  CheckCircle, 
  XCircle, 
  Activity, 
  Clock, 
  TrendingUp,
  Search,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';

function ServicesPage() {
  const [services] = useAtom(servicesAtom);
  const [filteredServices] = useAtom(filteredServicesAtom);
  const [serviceFilter, setServiceFilter] = useAtom(serviceFilterAtom);
  const [servicesLoading] = useAtom(servicesLoadingAtom);
  const [servicesError] = useAtom(servicesErrorAtom);

  const { refetch, isRefetching } = useServices();

  const getStatusColor = (health: boolean) => {
    return health ? 'text-green-600' : 'text-red-600';
  };

  const getStatusBadgeColor = (status: string, health: boolean) => {
    if (!health) return 'bg-red-100 text-red-800';
    
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800';
      case 'starting':
        return 'bg-yellow-100 text-yellow-800';
      case 'stopping':
        return 'bg-orange-100 text-orange-800';
      case 'stopped':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Services</h1>
            <p className="mt-2 text-gray-600">
              Monitor and manage AI agent services
            </p>
          </div>
          
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search services..."
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Services Grid */}
      {servicesLoading ? (
        <div className="text-center py-12">
          <Clock className="w-8 h-8 text-gray-400 mx-auto mb-4 animate-spin" />
          <p className="text-gray-500">Loading services...</p>
        </div>
      ) : servicesError ? (
        <div className="text-center py-12">
          <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-4">Error loading services</p>
          <p className="text-gray-500 text-sm">{servicesError}</p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      ) : filteredServices.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500">
            {services.length === 0 ? 'No services available' : 'No services match your filter'}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredServices.map((service) => (
            <div key={service.name} className="bg-white rounded-lg shadow p-6">
              {/* Service Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {service.health ? (
                    <CheckCircle className="w-6 h-6 text-green-500" />
                  ) : (
                    <XCircle className="w-6 h-6 text-red-500" />
                  )}
                  <h3 className="text-lg font-semibold text-gray-900 truncate">
                    {service.name}
                  </h3>
                </div>
                
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  getStatusBadgeColor(service.status, service.health)
                }`}>
                  {service.status}
                </span>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {service.metrics.total_requests}
                  </div>
                  <div className="text-sm text-gray-500">Total Requests</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {service.metrics.success_rate.toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-500">Success Rate</div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 flex items-center">
                    <Activity className="w-4 h-4 mr-2" />
                    Avg Response Time
                  </span>
                  <span className="text-sm font-medium">
                    {service.metrics.average_response_time.toFixed(2)}s
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 flex items-center">
                    <Clock className="w-4 h-4 mr-2" />
                    Uptime
                  </span>
                  <span className="text-sm font-medium">
                    {formatUptime(service.metrics.uptime_seconds)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 flex items-center">
                    <TrendingUp className="w-4 h-4 mr-2" />
                    Successful Requests
                  </span>
                  <span className="text-sm font-medium text-green-600">
                    {service.metrics.successful_requests}
                  </span>
                </div>

                {service.metrics.failed_requests > 0 && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 flex items-center">
                      <AlertTriangle className="w-4 h-4 mr-2" />
                      Failed Requests
                    </span>
                    <span className="text-sm font-medium text-red-600">
                      {service.metrics.failed_requests}
                    </span>
                  </div>
                )}
              </div>

              {/* Health Status Bar */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Health Status</span>
                  <span className={`font-medium ${getStatusColor(service.health)}`}>
                    {service.health ? 'Healthy' : 'Unhealthy'}
                  </span>
                </div>
                
                {/* Success Rate Progress Bar */}
                <div className="mt-2">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Success Rate</span>
                    <span>{service.metrics.success_rate.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        service.metrics.success_rate >= 95 ? 'bg-green-500' :
                        service.metrics.success_rate >= 80 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(service.metrics.success_rate, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary Statistics */}
      {services.length > 0 && (
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Summary Statistics</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {services.length}
              </div>
              <div className="text-sm text-gray-500">Total Services</div>
            </div>
            
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {services.filter(s => s.health).length}
              </div>
              <div className="text-sm text-gray-500">Healthy Services</div>
            </div>
            
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">
                {services.reduce((sum, s) => sum + s.metrics.total_requests, 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Total Requests</div>
            </div>
            
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">
                {services.length > 0 ? (
                  services.reduce((sum, s) => sum + s.metrics.success_rate, 0) / services.length
                ).toFixed(1) : '0'}%
              </div>
              <div className="text-sm text-gray-500">Avg Success Rate</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export const Route = createFileRoute('/services')({
  component: ServicesPage,
});