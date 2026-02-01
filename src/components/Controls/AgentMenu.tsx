import React from 'react';
import { ParameterSlider } from './ParameterSlider';
import { Scale, TrendingDown, TrendingUp, UserPlus, Users, Zap } from 'lucide-react';
import type { ClientAction, GroupConfig } from '../../types/simulation';

interface AgentMenuProps {
    onClose: () => void;
    sendAction: (action: ClientAction) => void;
    activeGroupId: number;
    existingGroupIds: number[];
}

export const AgentMenu: React.FC<AgentMenuProps> = ({
    onClose,
    sendAction,
    activeGroupId,
    existingGroupIds,
}) => {
    const [numAgents, setNumAgents] = React.useState(50);
    const [trustQuota, setTrustQuota] = React.useState(0.3);
    const [trustGain, setTrustGain] = React.useState(0.1);
    const [trustLoss, setTrustLoss] = React.useState(0.05);
    const [speedMultiplier, setSpeedMultiplier] = React.useState(1.0);
    const [createNewGroup, setCreateNewGroup] = React.useState(true);

    const nextGroupId = React.useMemo(() => {
        for (let i = 0; i < 5; i++) {
            if (!existingGroupIds.includes(i)) return i;
        }
        return -1;
    }, [existingGroupIds]);

    const handleDeploy = () => {
        if (createNewGroup && nextGroupId >= 0) {
            // Create new group with these agents and config
            sendAction({
                type: 'create_group',
                payload: {
                    groupId: nextGroupId,
                    numAgents,
                    config: {
                        trustQuota,
                        trustDecay: 0.05,
                        globalAlpha: trustGain,
                        globalBeta: trustLoss,
                        speedMultiplier,
                    },
                },
            });
        } else {
            // Add batch to active group
            sendAction({
                type: 'add_agent',
                payload: {
                    numAgents,
                    trustQuota,
                    trustGain,
                    trustLoss,
                    groupId: activeGroupId,
                },
            });
        }
    };

    const canCreateNew = nextGroupId >= 0;

    return (
        <div
            className="glass-panel"
            style={{
                position: 'absolute',
                top: 20,
                right: 340,
                height: 'auto',
                maxHeight: 'calc(80vh - 40px)',
                width: '220px',
                padding: '1rem',
                borderRadius: 'var(--radius-lg)',
                zIndex: 20,
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                overflowY: 'auto',
            }}
        >
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center' }}>
                <UserPlus size={20} style={{ marginRight: '0.5rem', color: 'var(--color-accent-primary)' }} />
                <span style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                    Deploy Agents
                </span>
                <div
                    onClick={onClose}
                    style={{ marginLeft: 'auto', cursor: 'pointer', fontSize: '1.2rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}
                >
                    &times;
                </div>
            </div>

            {/* Toggle: New Group vs Add to Current */}
            <div style={{
                display: 'flex',
                gap: '0.25rem',
                background: 'rgba(255,255,255,0.03)',
                borderRadius: 'var(--radius-md, 8px)',
                padding: '0.2rem',
            }}>
                <button
                    onClick={() => setCreateNewGroup(true)}
                    disabled={!canCreateNew}
                    style={{
                        flex: 1,
                        padding: '0.4rem',
                        border: 'none',
                        borderRadius: 'var(--radius-sm, 6px)',
                        cursor: canCreateNew ? 'pointer' : 'not-allowed',
                        fontSize: '0.75rem',
                        fontWeight: createNewGroup ? 700 : 500,
                        background: createNewGroup ? 'var(--color-accent-primary, #6366f1)' : 'transparent',
                        color: createNewGroup ? '#fff' : 'var(--color-text-secondary, #aaa)',
                        opacity: canCreateNew ? 1 : 0.4,
                    }}
                >
                    New Group
                </button>
                <button
                    onClick={() => setCreateNewGroup(false)}
                    style={{
                        flex: 1,
                        padding: '0.4rem',
                        border: 'none',
                        borderRadius: 'var(--radius-sm, 6px)',
                        cursor: 'pointer',
                        fontSize: '0.75rem',
                        fontWeight: !createNewGroup ? 700 : 500,
                        background: !createNewGroup ? 'var(--color-accent-primary, #6366f1)' : 'transparent',
                        color: !createNewGroup ? '#fff' : 'var(--color-text-secondary, #aaa)',
                    }}
                >
                    Add to G{activeGroupId}
                </button>
            </div>

            {createNewGroup && canCreateNew && (
                <div style={{
                    fontSize: '0.75rem',
                    color: 'var(--color-text-muted)',
                    textAlign: 'center',
                    padding: '0.25rem',
                    background: 'rgba(99, 102, 241, 0.1)',
                    borderRadius: 'var(--radius-sm, 6px)',
                }}>
                    Will create Group {nextGroupId}
                </div>
            )}

            <ParameterSlider
                label="Agent Count"
                icon={Users}
                onChange={(v) => setNumAgents(Math.round(v))}
                value={numAgents}
                min={1} max={500} step={1}
            />

            <ParameterSlider
                label="Trust Quota"
                icon={Scale}
                onChange={setTrustQuota}
                value={trustQuota}
                min={0} max={1} step={0.05}
            />

            <ParameterSlider
                label="Trust Gain"
                icon={TrendingUp}
                onChange={setTrustGain}
                value={trustGain}
                min={0} max={1} step={0.05}
            />

            <ParameterSlider
                label="Trust Loss"
                icon={TrendingDown}
                onChange={setTrustLoss}
                value={trustLoss}
                min={0} max={1} step={0.05}
            />

            <ParameterSlider
                label="Speed"
                icon={Zap}
                onChange={setSpeedMultiplier}
                value={speedMultiplier}
                min={0.1} max={5.0} step={0.1}
                unit="x"
            />

            <button
                onClick={handleDeploy}
                disabled={createNewGroup && !canCreateNew}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '0.6rem',
                    borderRadius: 'var(--radius-md)',
                    cursor: (createNewGroup && !canCreateNew) ? 'not-allowed' : 'pointer',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    transition: 'all 0.2s',
                    gap: '0.5rem',
                    background: 'rgba(34, 197, 94, 0.2)',
                    color: 'var(--color-success)',
                    border: '1px solid rgba(34, 197, 94, 0.5)',
                    opacity: (createNewGroup && !canCreateNew) ? 0.4 : 1,
                }}
            >
                <UserPlus size={18} />
                Deploy {numAgents} Agent{numAgents !== 1 ? 's' : ''}
            </button>
        </div>
    );
};