/**
 * Generated route tree for TanStack Router
 */

import { Route as rootRoute } from './routes/__root';
import { Route as indexRoute } from './routes/index';
import { Route as tasksRoute } from './routes/tasks';
import { Route as servicesRoute } from './routes/services';
import { Route as monitoringRoute } from './routes/monitoring';

export const routeTree = rootRoute.addChildren({
  '/': indexRoute,
  '/tasks': tasksRoute,
  '/services': servicesRoute,
  '/monitoring': monitoringRoute,
});