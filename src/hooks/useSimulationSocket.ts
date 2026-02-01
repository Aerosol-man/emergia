import { useEffect, useRef, useState, useCallback } from 'react';
import type { SimulationState, ClientAction, SimulationConfig, GroupData, GroupConfig } from '../types/simulation';

const createMockState = (tick: number, config: SimulationConfig, width: number, height: number): SimulationState => {
    const agents = [];
    const count = config.agentCount;
    const speed = 0.05 * config.speedMultiplier;
    const clusterTightness = config.softSeparation;
    const repulsionStrength = config.hardSeparation;

    for (let i = 0; i < count; i++) {
        const angle = (tick * speed) + (i * (Math.PI * 2 / count));
        const baseRadius = 100 + (config.trustQuota * 50);
        const separationOffset = (repulsionStrength * 5) - (clusterTightness * 15);
        const radius = baseRadius + (Math.sin(tick * 0.01 + i) * 50) + separationOffset;

        agents.push({
            id: i,
            x: (width / 2) + Math.cos(angle) * radius,
            y: (height / 2) + Math.sin(angle) * radius,
            vx: 0, vy: 0,
            trust: Math.max(0, ((Math.sin(tick * 0.02 + i) + 1) / 2) - config.trustDecay),
            trustQuota: config.trustQuota,
            skillPossessed: 0, skillNeeded: 0,
            tradeCount: Math.floor(Math.random() * 5),
            groupId: 0,
        });
    }

    const mockGroup: GroupData = {
        groupId: 0,
        agents,
        metrics: { avgTrust: 0.5, giniCoefficient: 0.2, tradeSuccessRate: 0.8 },
        config: {
            trustQuota: config.trustQuota,
            trustDecay: config.trustDecay,
            globalAlpha: 0.1,
            globalBeta: 0.05,
            speedMultiplier: config.speedMultiplier,
        },
        agentCount: count,
    };

    return {
        tick,
        activeGroupId: 0,
        groups: { '0': mockGroup },
        agents,
        metrics: { avgTrust: 0.5, giniCoefficient: 0.2, tradeSuccessRate: 0.8 },
    };
};

export const useSimulationSocket = (url: string = 'ws://localhost:8000/ws') => {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMetrics, setLastMetrics] = useState<SimulationState['metrics'] | null>(null);
    const [activeGroupId, setActiveGroupId] = useState(0);
    const [existingGroupIds, setExistingGroupIds] = useState<number[]>([0]);
    const [groupConfigs, setGroupConfigs] = useState<Record<number, GroupConfig>>({});
    const [visibleGroupIds, setVisibleGroupIds] = useState<Set<number>>(new Set([0]));

    const stateBuffer = useRef<SimulationState[]>([]);
    const allAgentsRef = useRef<SimulationState['agents']>([]);
    const socketRef = useRef<WebSocket | null>(null);

    const mockIntervalRef = useRef<number | null>(null);
    const mockConfigRef = useRef<SimulationConfig>({
        agentCount: 50, trustDecay: 0.0, trustQuota: 0.3,
        speedMultiplier: 1.0, softSeparation: 0.8, hardSeparation: 6.0
    });
    const isMock = false;

    const visibleGroupIdsRef = useRef(visibleGroupIds);
    visibleGroupIdsRef.current = visibleGroupIds;

    const handleStateUpdate = useCallback((newState: SimulationState) => {
        // Store all agents for reference
        allAgentsRef.current = newState.agents;

        // Filter agents to only visible groups for the renderer
        const visible = visibleGroupIdsRef.current;
        const filteredState = {
            ...newState,
            agents: newState.agents.filter(a => visible.has(a.groupId ?? 0)),
        };

        stateBuffer.current.push(filteredState);
        if (stateBuffer.current.length > 3) {
            stateBuffer.current.shift();
        }

        if (newState.activeGroupId !== undefined) {
            setActiveGroupId(newState.activeGroupId);
        }
        if (newState.groups) {
            const ids = Object.keys(newState.groups).map(Number);
            setExistingGroupIds(ids);

            // Auto-mark new groups as visible
            setVisibleGroupIds(prev => {
                const next = new Set(prev);
                let changed = false;
                for (const id of ids) {
                    if (!next.has(id)) {
                        next.add(id);
                        changed = true;
                    }
                }
                return changed ? next : prev;
            });

            const configs: Record<number, GroupConfig> = {};
            for (const [gid, group] of Object.entries(newState.groups)) {
                if (group.config) {
                    configs[Number(gid)] = group.config;
                }
            }
            setGroupConfigs(configs);
        }

        if (newState.tick % 10 === 0) {
            setLastMetrics(newState.metrics);
        }
    }, []);

    useEffect(() => {
        if (isMock) {
            setIsConnected(true);
            let tick = 0;
            mockIntervalRef.current = window.setInterval(() => {
                tick++;
                handleStateUpdate(createMockState(tick, mockConfigRef.current, 800, 600));
            }, 33);
            return () => { if (mockIntervalRef.current) clearInterval(mockIntervalRef.current); };
        }

        let cancelled = false;
        let ws: WebSocket | null = null;

        const timeoutId = setTimeout(() => {
            if (cancelled) return;
            ws = new WebSocket(url);
            socketRef.current = ws;

            ws.onopen = () => {
                if (cancelled) { ws?.close(); return; }
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

                    if (!stateBuffer.current.length || stateBuffer.current.length < 3) {
                        console.log('[WS] Received:', data.type, 'agents:', data.payload?.agents?.length);
                    }

                    if (data.type === 'state_update' && data.payload) {
                        handleStateUpdate(data.payload);
                    }
                    if (data.type === 'group_created') {
                        console.log('[WS] Group created:', data.payload);
                    }
                    if (data.type === 'group_switched' && data.payload?.activeGroupId !== undefined) {
                        setActiveGroupId(data.payload.activeGroupId);
                    }
                    if (data.type === 'group_config_updated') {
                        console.log('[WS] Group config updated:', data.payload);
                    }
                } catch (e) {
                    console.error('[WS] Failed to parse message', e);
                }
            };
        }, 50);

        return () => {
            cancelled = true;
            clearTimeout(timeoutId);
            if (ws) {
                ws.onopen = null; ws.onclose = null;
                ws.onerror = null; ws.onmessage = null;
                ws.close();
            }
            socketRef.current = null;
        };
    }, [url, handleStateUpdate]);

    const sendAction = useCallback((action: ClientAction) => {
        if (isMock) {
            if (action.type === 'update_config' && action.payload) {
                mockConfigRef.current = { ...mockConfigRef.current, ...action.payload };
            }
            if (action.type === 'pause' && mockIntervalRef.current) clearInterval(mockIntervalRef.current);
            if (action.type === 'start') {
                if (mockIntervalRef.current) clearInterval(mockIntervalRef.current);
                let tick = 0;
                mockIntervalRef.current = window.setInterval(() => {
                    tick++;
                    handleStateUpdate(createMockState(tick, mockConfigRef.current, 800, 600));
                }, 33);
            }
            return;
        }
        const socket = socketRef.current;
        if (socket && socket.readyState === WebSocket.OPEN) {
            console.log('[WS] Sending:', action);
            socket.send(JSON.stringify(action));
        } else {
            console.warn('[WS] Cannot send, socket not open.');
        }
    }, [isMock, handleStateUpdate]);

    const switchGroup = useCallback((groupId: number) => {
        sendAction({ type: 'switch_group', payload: { groupId } });
        setActiveGroupId(groupId);
    }, [sendAction]);

    const createGroup = useCallback((groupId: number, numAgents: number, config?: Partial<GroupConfig>) => {
        sendAction({ type: 'create_group', payload: { groupId, numAgents, config } });
    }, [sendAction]);

    const updateGroupConfig = useCallback((groupId: number, config: Partial<GroupConfig>) => {
        sendAction({ type: 'update_group_config', payload: { groupId, config } });
    }, [sendAction]);

    const toggleGroupVisibility = useCallback((groupId: number) => {
        setVisibleGroupIds(prev => {
            const next = new Set(prev);
            if (next.has(groupId)) {
                next.delete(groupId);
            } else {
                next.add(groupId);
            }
            return next;
        });
    }, []);

    return {
        isConnected,
        lastMetrics,
        agents: stateBuffer.current[stateBuffer.current.length - 1]?.agents || [],
        stateBuffer,
        sendAction,
        activeGroupId,
        existingGroupIds,
        groupConfigs,
        visibleGroupIds,
        switchGroup,
        createGroup,
        updateGroupConfig,
        toggleGroupVisibility,
    };
};