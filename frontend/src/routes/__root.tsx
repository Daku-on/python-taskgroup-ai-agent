/**
 * Root route for TanStack Router
 */

import { createRootRoute, Link, Outlet } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/router-devtools';
import { Activity, Bot, Database, BarChart3, Home } from 'lucide-react';
import { WebSocketProvider } from '../components/WebSocketProvider';
import { NotificationToast } from '../components/NotificationToast';

export const Route = createRootRoute({
  component: () => (
    <WebSocketProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <Bot className="h-8 w-8 text-blue-600" />
                  <span className="ml-2 text-xl font-bold text-gray-900">
                    AI Agent Dashboard
                  </span>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  <Link
                    to="/"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300 [&.active]:border-blue-500 [&.active]:text-blue-600"
                  >
                    <Home className="w-4 h-4 mr-2" />
                    Dashboard
                  </Link>
                  <Link
                    to="/tasks"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300 [&.active]:border-blue-500 [&.active]:text-blue-600"
                  >
                    <Activity className="w-4 h-4 mr-2" />
                    Tasks
                  </Link>
                  <Link
                    to="/services"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300 [&.active]:border-blue-500 [&.active]:text-blue-600"
                  >
                    <Database className="w-4 h-4 mr-2" />
                    Services
                  </Link>
                  <Link
                    to="/monitoring"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300 [&.active]:border-blue-500 [&.active]:text-blue-600"
                  >
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Monitoring
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>

        {/* Toast notifications */}
        <NotificationToast />

        {/* Router devtools */}
        <TanStackRouterDevtools />
      </div>
    </WebSocketProvider>
  ),
});