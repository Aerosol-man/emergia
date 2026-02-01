import { useEffect, useRef, useState, useCallback } from 'react';
import type { SimulationState, WebSocketMessage, ClientAction, SimulationConfig } from '../types/simulation';

// Mock Data Generator for Dev Mode
const createMockState = (tick: number, config: SimulationConfig, width: number, height: number): SimulationState => {
    const agents = [];
    const count = config.agentCount;

    // Scale speed by multiplier
    const speed = 0.05 * config.speedMultiplier;

    // Use separation values to influence mock clustering behaviour
    const clusterTightness = config.softSeparation;   // higher = agents clump closer after good trades
    const repulsionStrength = config.hardSeparation;   // higher = agents spread further after bad trades

    for (let i = 0; i < count; i++) {
        const angle = (tick * speed) + (i * (Math.PI * 2 / count));

        // Base radius influenced by softSeparation (stickiness shrinks radius)
        // and hardSeparation (repulsion expands it)
        const baseRadius = 100 + (config.trustQuota * 50);
        const separationOffset = (repulsionStrength * 5) - (clusterTightness * 15);
        const radius = baseRadius + (Math.sin(tick * 0.01 + i) * 50) + separationOffset;

        agents.push({
            id: i,
            x: (width / 2) + Math.cos(angle) * radius,
            y: (height / 2) + Math.sin(angle) * radius,
            vx: 0,
            vy: 0,
            trust: Math.max(0, ((Math.sin(tick * 0.02 + i) + 1) / 2) - config.trustDecay),
            trustQuota: config.trustQuota,
            skillPossessed: 0,
            skillNeeded: 0,
            tradeCount: Math.floor(Math.random() * 5)
        });
    }

    return {
        tick,
        agents,
        metrics: {
            avgTrust: 0.5,
            giniCoefficient: 0.2,
            tradeSuccessRate: 0.8
        }
    };
};

export const useSimulationSocket = (url: string = 'ws://localhost:8000/ws') => {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMetrics, setLastMetrics] = useState<SimulationState['metrics'] | null>(null);

    const stateBuffer = useRef<SimulationState[]>([]);
    const socketRef = useRef<WebSocket | null>(null);

    // Mock Mode Logic
    const mockIntervalRef = useRef<number | null>(null);
    const mockConfigRef = useRef<SimulationConfig>({
        agentCount: 50,
        trustDecay: 0.0,
        trustQuota: 0.3,
        speedMultiplier: 1.0,
        softSeparation: 0.8,
        hardSeparation: 6.0
    });
    const isMock = false;

    const handleStateUpdate = useCallback((newState: SimulationState) => {
        stateBuffer.current.push(newState);

        if (stateBuffer.current.length > 3) {
            stateBuffer.current.shift();
        }

        if (newState.tick % 10 === 0) {
            setLastMetrics(newState.metrics);
        }
    }, []);

    useEffect(() => {
        if (isMock) {
            console.log('Starting Mock Simulation Mode');
            setIsConnected(true);
            let tick = 0;

            mockIntervalRef.current = window.setInterval(() => {
                tick++;
                const newState = createMockState(tick, mockConfigRef.current, 800, 600);
                handleStateUpdate(newState);
            }, 33);

            return () => {
                if (mockIntervalRef.current) clearInterval(mockIntervalRef.current);
            };
        }

        // Real WebSocket Implementation
        let cancelled = false;
        let ws: WebSocket | null = null;

        const timeoutId = setTimeout(() => {
            if (cancelled) return;

            ws = new WebSocket(url);
            socketRef.current = ws;

            ws.onopen = () => {
                if (cancelled) {
                    ws?.close();
                    return;
                }
                console.log('[WS] Connected');
                setIsConnected(true);
            };

            ws.onclose = (e) => {
                if (cancelled) return;
                console.log('[WS] Disconnected', e.code, e.reason);
                setIsConnected(false);
            };

            ws.onerror = (err) => {
                if (cancelled) return;
                console.error('[WS] Error:', err);
            };

            ws.onmessage = (event) => {
                if (cancelled) return;
                try {
                    const data = JSON.parse(event.data);

                    // DEBUG: log first few messages
                    if (!stateBuffer.current.length || stateBuffer.current.length < 3) {
                        console.log('[WS] Received:', data.type, 'agents:', data.payload?.agents?.length);
                    }

                    // The backend sends { type: "state_update", payload: { tick, agents, metrics, bounds } }
                    if (data.type === 'state_update' && data.payload) {
                        handleStateUpdate(data.payload);
                    }
                } catch (e) {
                    console.error('[WS] Failed to parse message', e);
                }
            };
        }, 50); // Small delay to avoid React Strict Mode double-mount issue

        return () => {
            cancelled = true;
            clearTimeout(timeoutId);
            if (ws) {
                ws.onopen = null;
                ws.onclose = null;
                ws.onerror = null;
                ws.onmessage = null;
                ws.close();
            }
            socketRef.current = null;
        };
    }, [url, handleStateUpdate]);

    const sendAction = useCallback((action: ClientAction) => {
        if (isMock) {
            console.log('Mock Action:', action);
            if (action.type === 'update_config' && action.payload) {
                mockConfigRef.current = { ...mockConfigRef.current, ...action.payload };
            }
            if (action.type === 'pause') {
                if (mockIntervalRef.current) clearInterval(mockIntervalRef.current);
            }
            if (action.type === 'start') {
                if (mockIntervalRef.current) clearInterval(mockIntervalRef.current);
                let tick = 0;
                mockIntervalRef.current = window.setInterval(() => {
                    tick++;
                    const newState = createMockState(tick, mockConfigRef.current, 800, 600);
                    handleStateUpdate(newState);
                }, 33);
            }
            return;
        }

        const socket = socketRef.current;
        if (socket && socket.readyState === WebSocket.OPEN) {
            console.log('[WS] Sending:', action);
            socket.send(JSON.stringify(action));
        } else {
            console.warn('[WS] Cannot send, socket not open. readyState:', socket?.readyState);
        }
    }, [isMock, handleStateUpdate]);

    return {
        isConnected,
        lastMetrics,
        stateBuffer,
        sendAction
    };
};