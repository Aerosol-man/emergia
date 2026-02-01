export interface Agent {
    id: number;
    x: number;
    y: number;
    vx: number;
    vy: number;
    trust: number;
    trustQuota: number;
    skillPossessed: number;
    skillNeeded: number;
    tradeCount: number;
    isCustom?: boolean;
    groupId: number;
}

export interface GroupConfig {
    trustQuota: number;
    trustDecay: number;
    globalAlpha: number;
    globalBeta: number;
    speedMultiplier: number;
}

export interface GroupData {
    groupId: number;
    agents: Agent[];
    metrics: SimulationMetrics;
    config: GroupConfig;
    agentCount: number;
}

export interface SimulationMetrics {
    avgTrust: number;
    giniCoefficient: number;
    tradeSuccessRate: number;
    tradeCount?: number;
    totalCollisions?: number;
}

export interface SimulationState {
    tick: number;
    activeGroupId: number;
    groups: Record<string, GroupData>;
    agents: Agent[];
    metrics: SimulationMetrics;
    bounds?: [number, number];
}

export interface SimulationConfig {
    agentCount: number;
    trustDecay: number;
    trustQuota: number;
    speedMultiplier: number;
    softSeparation: number;
    hardSeparation: number;
}

export type WebSocketMessage =
    | { type: 'state_update'; payload: SimulationState }
    | { type: 'group_created'; payload: { status: string; groupId: number; agentCount: number; config: GroupConfig } | { error: string } }
    | { type: 'group_switched'; payload: { status: string; activeGroupId: number } | { error: string } }
    | { type: 'group_config_updated'; payload: { status: string; groupId: number; config: GroupConfig } | { error: string } }
    | { type: 'event'; payload: { name: string; details: any } };

export type ClientAction =
    | { type: 'start'; payload: SimulationConfig }
    | { type: 'pause' }
    | { type: 'reset' }
    | { type: 'update_config'; payload: Partial<SimulationConfig> }
    | { type: 'add_agent'; payload: { numAgents: number; trustQuota: number; trustGain: number; trustLoss: number; groupId?: number } }
    | { type: 'create_group'; payload: { groupId: number; numAgents: number; config?: Partial<GroupConfig> } }
    | { type: 'switch_group'; payload: { groupId: number } }
    | { type: 'update_group_config'; payload: { groupId: number; config: Partial<GroupConfig> } };