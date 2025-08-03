/**
 * TanStack Query hooks for API calls
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAtom } from 'jotai';
import { api } from '../api/client';
import type { TaskRequest, WorkflowRequest } from '../types/api';
import { 
  addTaskToHistoryAtom, 
  addNotificationAtom,
  updateServiceStatusAtom,
  setServicesErrorAtom,
  setServicesLoadingAtom
} from '../stores/atoms';

// Query keys
export const queryKeys = {
  health: ['health'] as const,
  services: ['services'] as const,
  tasks: ['tasks'] as const,
} as const;

// Health check hook
export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => api.health(),
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 3,
    staleTime: 10000, // Consider data stale after 10 seconds
  });
}

// Services status hook
export function useServices() {
  const [, updateServiceStatus] = useAtom(updateServiceStatusAtom);
  const [, setServicesError] = useAtom(setServicesErrorAtom);
  const [, setServicesLoading] = useAtom(setServicesLoadingAtom);

  return useQuery({
    queryKey: queryKeys.services,
    queryFn: async () => {
      setServicesLoading(true);
      const response = await api.getServices();
      
      if (response.error) {
        setServicesError(response.error);
        throw new Error(response.error);
      }
      
      if (response.data) {
        updateServiceStatus(response.data);
      }
      
      return response.data || [];
    },
    refetchInterval: 5000, // Refetch every 5 seconds
    retry: 2,
    staleTime: 2000,
  });
}

// Task execution hook
export function useExecuteTask() {
  const queryClient = useQueryClient();
  const [, addTaskToHistory] = useAtom(addTaskToHistoryAtom);
  const [, addNotification] = useAtom(addNotificationAtom);

  return useMutation({
    mutationFn: (request: TaskRequest) => api.executeTask(request),
    onSuccess: (result) => {
      if (result.data) {
        addTaskToHistory(result.data);
        addNotification({
          type: 'success',
          message: `Task "${result.data.name}" completed successfully`,
        });
      }
      
      // Invalidate and refetch services to update metrics
      queryClient.invalidateQueries({ queryKey: queryKeys.services });
    },
    onError: (error: any, variables) => {
      addNotification({
        type: 'error',
        message: `Task "${variables.name}" failed: ${error.message || 'Unknown error'}`,
      });
    },
  });
}

// Workflow execution hook  
export function useExecuteWorkflow() {
  const queryClient = useQueryClient();
  const [, addNotification] = useAtom(addNotificationAtom);

  return useMutation({
    mutationFn: (request: WorkflowRequest) => api.executeWorkflow(request),
    onSuccess: (response, variables) => {
      addNotification({
        type: 'success',
        message: `Workflow "${variables.name}" completed successfully`,
      });
      
      // Invalidate and refetch services
      queryClient.invalidateQueries({ queryKey: queryKeys.services });
    },
    onError: (error: any, variables) => {
      addNotification({
        type: 'error',
        message: `Workflow "${variables.name}" failed: ${error.message || 'Unknown error'}`,
      });
    },
  });
}

// Custom hook for real-time updates
export function useRealTimeUpdates() {
  const queryClient = useQueryClient();
  const [, addNotification] = useAtom(addNotificationAtom);

  const handleWebSocketMessage = (data: any) => {
    try {
      if (data.type === 'status_update') {
        // Refresh services data when status updates come in
        queryClient.invalidateQueries({ queryKey: queryKeys.services });
      } else if (data.type === 'task_completed') {
        addNotification({
          type: 'info',
          message: `Task completed: ${data.task_name || 'Unknown task'}`,
        });
        queryClient.invalidateQueries({ queryKey: queryKeys.services });
      } else if (data.type === 'workflow_completed') {
        addNotification({
          type: 'info',
          message: `Workflow completed: ${data.workflow_name || 'Unknown workflow'}`,
        });
        queryClient.invalidateQueries({ queryKey: queryKeys.services });
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  };

  return { handleWebSocketMessage };
}

// Prefetch hooks for performance
export function usePrefetchData() {
  const queryClient = useQueryClient();

  const prefetchServices = () => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.services,
      queryFn: () => api.getServices(),
      staleTime: 2000,
    });
  };

  const prefetchHealth = () => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.health,
      queryFn: () => api.health(),
      staleTime: 10000,
    });
  };

  return { prefetchServices, prefetchHealth };
}