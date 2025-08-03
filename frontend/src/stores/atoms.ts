/**
 * Jotai atoms for state management
 */

import { atom } from 'jotai';
import type { ServiceStatus, TaskResponse } from '../types/api';

// サービス状態
export const servicesAtom = atom<ServiceStatus[]>([]);
export const servicesLoadingAtom = atom<boolean>(false);
export const servicesErrorAtom = atom<string | null>(null);

// タスク履歴
export const taskHistoryAtom = atom<TaskResponse[]>([]);
export const currentTaskAtom = atom<TaskResponse | null>(null);
export const taskLoadingAtom = atom<boolean>(false);

// アプリケーション状態
export const selectedAgentTypeAtom = atom<'llm' | 'database' | 'rag'>('llm');
export const connectionStatusAtom = atom<'connected' | 'disconnected' | 'connecting'>('disconnected');
export const notificationsAtom = atom<Array<{
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  timestamp: Date;
}>>([]);

// フィルターとソート
export const serviceFilterAtom = atom<string>('');
export const taskFilterAtom = atom<'all' | 'completed' | 'failed'>('all');

// 導出アトム（computed values）
export const filteredServicesAtom = atom(
  (get) => {
    const services = get(servicesAtom);
    const filter = get(serviceFilterAtom);
    
    if (!filter) return services;
    
    return services.filter(service => 
      service.name.toLowerCase().includes(filter.toLowerCase()) ||
      service.status.toLowerCase().includes(filter.toLowerCase())
    );
  }
);

export const filteredTaskHistoryAtom = atom(
  (get) => {
    const tasks = get(taskHistoryAtom);
    const filter = get(taskFilterAtom);
    
    if (filter === 'all') return tasks;
    
    return tasks.filter(task => task.status === filter);
  }
);

export const healthyServicesCountAtom = atom(
  (get) => {
    const services = get(servicesAtom);
    return services.filter(service => service.health).length;
  }
);

export const totalRequestsAtom = atom(
  (get) => {
    const services = get(servicesAtom);
    return services.reduce((total, service) => 
      total + service.metrics.total_requests, 0
    );
  }
);

// Actions (write-only atoms)
export const addTaskToHistoryAtom = atom(
  null,
  (get, set, task: TaskResponse) => {
    const currentHistory = get(taskHistoryAtom);
    set(taskHistoryAtom, [task, ...currentHistory.slice(0, 99)]); // Keep last 100 tasks
  }
);

export const addNotificationAtom = atom(
  null,
  (get, set, notification: { type: 'success' | 'error' | 'info' | 'warning'; message: string }) => {
    const currentNotifications = get(notificationsAtom);
    const newNotification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date(),
    };
    
    set(notificationsAtom, [newNotification, ...currentNotifications.slice(0, 9)]); // Keep last 10 notifications
    
    // Auto-remove notification after 5 seconds
    setTimeout(() => {
      set(notificationsAtom, (prev) => 
        prev.filter(n => n.id !== newNotification.id)
      );
    }, 5000);
  }
);

export const removeNotificationAtom = atom(
  null,
  (_get, set, id: string) => {
    set(notificationsAtom, (prev) => prev.filter(n => n.id !== id));
  }
);

export const updateServiceStatusAtom = atom(
  null,
  (_get, set, services: ServiceStatus[]) => {
    set(servicesAtom, services);
    set(servicesLoadingAtom, false);
    set(servicesErrorAtom, null);
  }
);

export const setServicesErrorAtom = atom(
  null,
  (_get, set, error: string) => {
    set(servicesErrorAtom, error);
    set(servicesLoadingAtom, false);
  }
);

export const setServicesLoadingAtom = atom(
  null,
  (_get, set, loading: boolean) => {
    set(servicesLoadingAtom, loading);
    if (loading) {
      set(servicesErrorAtom, null);
    }
  }
);