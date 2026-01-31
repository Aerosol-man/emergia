export interface Agent {
    id: number;
    x: number;
    y: number;
    vx: number;
    vy: number;
    trust: number;       // 0.0 to 1.0
    trustQuota: number;
    skillPossessed: number;
    skillNeeded: number;
    tradeCount: number;
}

export interface SimulationState {
    tick: number;
    agents: Agent[];
    metrics: {
        avgTrust: number;
        giniCoefficient: number;
        tradeSuccessRate: number;
    };
    bounds?: [number, number]; // [width, height] from server
}

export interface SimulationConfig {
    agentCount: number;
    trustDecay: number;
    trustQuota: number;
    speedMultiplier: number;
}

/**
* Message format from WebSocket
*/
export type WebSocketMessage =
    | { type: 'state_update'; payload: SimulationState }
    | { type: 'event'; payload: { name: string; details: any } };

/**
* Message format to WebSocket
*/
export type ClientAction =
    | { type: 'start' }
    | { type: 'pause' }
    | { type: 'reset' }
    | { type: 'update_config'; payload: Partial<SimulationConfig> };
