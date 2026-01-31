import { useEffect, useRef, useState, useCallback } from 'react';
import type { SimulationState, WebSocketMessage, ClientAction, SimulationConfig } from '../types/simulation';

// Mock Data Generator for Dev Mode
const createMockState = (tick: number, config: SimulationConfig, width: number, height: number): SimulationState => {
    const agents = [];
    const count = config.agentCount;

    // Scale speed by multiplier
    const speed = 0.05 * config.speedMultiplier;

    for (let i = 0; i < count; i++) {
        // Simple circular motion for testing interpolation
        // We use tick * speed to control velocity
        const angle = (tick * speed) + (i * (Math.PI * 2 / count));

        // Radius expands with Trust Quota just to visualize it changing
        const radius = 100 + (Math.sin(tick * 0.01 + i) * 50) + (config.trustQuota * 50);

        agents.push({
            id: i,
            x: (width / 2) + Math.cos(angle) * radius,
            y: (height / 2) + Math.sin(angle) * radius,
            vx: 0,
            vy: 0,
            // Trust affected by decay
            trust: Math.max(0, ((Math.sin(tick * 0.02 + i) + 1) / 2) - config.trustDecay),
            trustQuota: config.trustQuota,
            skillPossessed: 0,
            skillNeeded: 0,
            tradeCount: Math.floor(Math.random() * 5) // Static for now
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

    // We store states in a buffer for interpolation
    // Buffer = [Older State, Newer State]
    const stateBuffer = useRef<SimulationState[]>([]);

    const socketRef = useRef<WebSocket | null>(null);

    // Mock Mode Logic
    const mockIntervalRef = useRef<number | null>(null);
    const mockConfigRef = useRef<SimulationConfig>({
        agentCount: 50,
        trustDecay: 0.0,
        trustQuota: 0.3,
        speedMultiplier: 1.0
    });
    const isMock = true; // Hardcoded for now until real backend is ready

    useEffect(() => {
        if (isMock) {
            console.log('Starting Mock Simulation Mode');
            setIsConnected(true);
            let tick = 0;

            mockIntervalRef.current = window.setInterval(() => {
                tick++;
                // Assume 800x600 for mock generation, renderer will scale visualization
                const newState = createMockState(tick, mockConfigRef.current, 800, 600);
                handleStateUpdate(newState);
            }, 33); // ~30Hz

            return () => {
                if (mockIntervalRef.current) clearInterval(mockIntervalRef.current);
            };
        }

        // Real WebSocket Implementation
        const ws = new WebSocket(url);
        socketRef.current = ws;

        ws.onopen = () => setIsConnected(true);
        ws.onclose = () => setIsConnected(false);
        ws.onmessage = (event) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data);
                if (message.type === 'state_update') {
                    handleStateUpdate(message.payload);
                }
            } catch (e) {
                console.error('Failed to parse WS message', e);
            }
        };

        return () => ws.close();
    }, [url]);

    const handleStateUpdate = useCallback((newState: SimulationState) => {
        // Push to buffer
        stateBuffer.current.push(newState);

        // Keep buffer small (max 3 states: [Old, Mid, New])
        if (stateBuffer.current.length > 3) {
            stateBuffer.current.shift();
        }

        // Update React State for UI (throttled naturally by how often we call this? No, this runs 30hz)
        // We should verify performance of this. ideally only update metrics every second.
        // For now, let's just set it.
        if (newState.tick % 10 === 0) {
            setLastMetrics(newState.metrics);
        }
    }, []);

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
                // Restart loop (simplified for mock)
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
        socketRef.current?.send(JSON.stringify(action));
    }, [isMock, handleStateUpdate]);

    return {
        isConnected,
        lastMetrics,
        stateBuffer, // Expose buffer to Renderer
        sendAction
    };
};
