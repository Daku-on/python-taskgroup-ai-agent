/**
 * WebSocket provider for real-time updates
 */

import { useEffect, useRef } from 'react';
import { useAtom } from 'jotai';
import { connectionStatusAtom, addNotificationAtom } from '../stores/atoms';
import { WebSocketManager } from '../api/client';
import { useRealTimeUpdates } from '../hooks/useApi';

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [, setConnectionStatus] = useAtom(connectionStatusAtom);
  const [, addNotification] = useAtom(addNotificationAtom);
  const wsManager = useRef<WebSocketManager | null>(null);
  const { handleWebSocketMessage } = useRealTimeUpdates();

  useEffect(() => {
    // Initialize WebSocket connection
    wsManager.current = new WebSocketManager();
    
    const connect = async () => {
      if (!wsManager.current) return;
      
      setConnectionStatus('connecting');
      
      try {
        await wsManager.current.connect();
        setConnectionStatus('connected');
        
        addNotification({
          type: 'success',
          message: 'Connected to real-time updates',
        });

        // Add message listener
        wsManager.current.addListener(handleWebSocketMessage);
        
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setConnectionStatus('disconnected');
        
        addNotification({
          type: 'error',
          message: 'Failed to connect to real-time updates',
        });
      }
    };

    // Initial connection
    connect();

    // Cleanup on unmount
    return () => {
      if (wsManager.current) {
        wsManager.current.disconnect();
        setConnectionStatus('disconnected');
      }
    };
  }, [setConnectionStatus, addNotification, handleWebSocketMessage]);

  // Monitor connection status
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsManager.current) {
        const isConnected = wsManager.current.isConnected();
        setConnectionStatus(isConnected ? 'connected' : 'disconnected');
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [setConnectionStatus]);

  return <>{children}</>;
}