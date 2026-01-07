import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const useWebSocket = (url: string, options: UseWebSocketOptions = {}) => {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const clientId = useRef(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');
    
    try {
      const wsUrl = `${url}?client_id=${clientId.current}`;
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('🔌 WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        setReconnectAttempts(0);
        onConnect?.();
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        onDisconnect?.();

        // Attempt to reconnect if not a manual close
        if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
          console.log(`🔄 Attempting to reconnect... (${reconnectAttempts + 1}/${maxReconnectAttempts})`);
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connect();
          }, reconnectInterval);
        }
      };

      ws.current.onerror = (error) => {
        console.error('🔌 WebSocket error:', error);
        setConnectionStatus('error');
        onError?.(error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('error');
    }
  }, [url, onMessage, onConnect, onDisconnect, onError, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (ws.current) {
      ws.current.close(1000, 'Manual disconnect');
      ws.current = null;
    }

    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
      return true;
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
      return false;
    }
  }, []);

  const sendPing = useCallback(() => {
    return sendMessage({ type: 'ping', timestamp: new Date().toISOString() });
  }, [sendMessage]);

  const subscribeToIncident = useCallback((incidentId: string) => {
    return sendMessage({ type: 'subscribe', incident_id: incidentId });
  }, [sendMessage]);

  const unsubscribeFromIncident = useCallback((incidentId: string) => {
    return sendMessage({ type: 'unsubscribe', incident_id: incidentId });
  }, [sendMessage]);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, []);

  // Ping every 30 seconds to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      sendPing();
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [isConnected, sendPing]);

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    reconnectAttempts,
    connect,
    disconnect,
    sendMessage,
    sendPing,
    subscribeToIncident,
    unsubscribeFromIncident
  };
};

// Hook specifically for dashboard real-time updates
export const useDashboardWebSocket = () => {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [systemAlerts, setSystemAlerts] = useState<any[]>([]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'incident_update':
        console.log('📊 Received incident update:', message.event_type, message.incident?.title);
        
        // Update incidents list
        setIncidents(prev => {
          const existingIndex = prev.findIndex(inc => inc.id === message.incident?.id);
          if (existingIndex >= 0) {
            const updated = [...prev];
            updated[existingIndex] = { ...updated[existingIndex], ...message.incident };
            return updated;
          } else {
            return [message.incident, ...prev].slice(0, 10); // Keep only latest 10
          }
        });
        break;

      case 'metrics_update':
        console.log('📈 Received metrics update');
        setMetrics(message.metrics);
        break;

      case 'system_alert':
        console.log('🚨 Received system alert:', message.alert_type);
        const alert = {
          id: Date.now(),
          type: message.alert_type,
          message: message.message,
          severity: message.severity,
          timestamp: message.timestamp
        };
        
        setSystemAlerts(prev => [alert, ...prev].slice(0, 5)); // Keep only latest 5
        
        // Auto-remove alert after 10 seconds
        setTimeout(() => {
          setSystemAlerts(prev => prev.filter(a => a.id !== alert.id));
        }, 10000);
        break;

      case 'heartbeat':
        console.log('💓 Heartbeat received, active connections:', message.active_connections);
        break;

      case 'connection_established':
        console.log('✅ WebSocket connection established:', message.client_id);
        break;

      default:
        console.log('📨 Unknown message type:', message.type);
    }
  }, []);

  const webSocket = useWebSocket('ws://localhost:8000/ws', {
    onMessage: handleMessage,
    onConnect: () => console.log('🔌 Dashboard WebSocket connected'),
    onDisconnect: () => console.log('🔌 Dashboard WebSocket disconnected'),
    onError: (error) => console.error('🔌 Dashboard WebSocket error:', error)
  });

  const clearAlert = useCallback((alertId: number) => {
    setSystemAlerts(prev => prev.filter(alert => alert.id !== alertId));
  }, []);

  return {
    ...webSocket,
    incidents,
    metrics,
    systemAlerts,
    clearAlert,
    setIncidents,
    setMetrics
  };
};