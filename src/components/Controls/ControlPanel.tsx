import React, { useState } from 'react';
import { ParameterSlider } from './ParameterSlider';
import { ActionGroup } from './ActionGroup';
import { Users, TrendingDown, ShieldCheck, ChevronDown, ChevronUp, Zap, UserPlus, Activity } from 'lucide-react';
import { AgentMenu } from './AgentMenu';
import { GroupToggle } from './GroupToggle';
import { CustomAgentDisplay } from '../Dashboard/CustomAgentDisplay';
import type { ClientAction, SimulationConfig, GroupConfig } from '../../types/simulation';

interface ControlPanelProps {
    sendAction: (action: ClientAction) => void;
    agents?: any[];
    activeGroupId: number;
    existingGroupIds: number[];
    groupConfigs: Record<number, GroupConfig>;
    visibleGroupIds: Set<number>;
    switchGroup: (groupId: number) => void;
    updateGroupConfig: (groupId: number, config: Partial<GroupConfig>) => void;
    toggleGroupVisibility: (groupId: number) => void;
    highlightedGroupId: number | null;
    setHighlightedGroupId: (id: number | null) => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
    sendAction,
    agents = [],
    activeGroupId,
    existingGroupIds,
    groupConfigs,
    visibleGroupIds,
    switchGroup,
    updateGroupConfig,
    toggleGroupVisibility,
    highlightedGroupId,
    setHighlightedGroupId,
}) => {
    const [config, setConfig] = useState<SimulationConfig>({
        agentCount: 500,
        trustDecay: 0.05,
        trustQuota: 0.3,
        speedMultiplier: 1.0,
        softSeparation: 0.8,
        hardSeparation: 6.0,
    });

    const [isRunning, setIsRunning] = useState(false);
    const [maximized, setMaximized] = useState(true);
    const [agentMenuOpen, setAgentMenuOpen] = useState(false);
    const [customAgentDisplayOpen, setCustomAgentDisplayOpen] = useState(false);

    // Get the active group's config for slider values
    const activeConfig = groupConfigs[activeGroupId];

    const handleChange = (key: keyof SimulationConfig, value: number) => {
        const newConfig = { ...config, [key]: value };
        setConfig(newConfig);

        // Send as global update_config (affects active group via backend)
        sendAction({ type: 'update_config', payload: { [key]: value } });
    };

    // Per-group config change — sends update_group_config
    const handleGroupConfigChange = (key: keyof GroupConfig, value: number) => {
        updateGroupConfig(activeGroupId, { [key]: value });
    };

    const handleStart = () => {
        setIsRunning(true);
        sendAction({ type: 'start', payload: config });
    };
    const handlePause = () => {
        setIsRunning(false);
        sendAction({ type: 'pause' });
    };
    const handleReset = () => {
        setIsRunning(false);
        sendAction({ type: 'reset' });
    };

    const toggleButton = (
        <div
            onClick={() => setMaximized(!maximized)}
            style={{
                cursor: 'pointer', padding: '0.5rem', borderRadius: '50%',
                background: 'var(--bg-accent-secondary)', boxShadow: 'var(--shadow-md)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 0,
            }}
        >
            {maximized
                ? <ChevronUp size={20} style={{ color: 'var(--color-text-primary)' }} />
                : <ChevronDown size={20} style={{ color: 'var(--color-text-primary)' }} />}
        </div>
    );

    const agentButton = (
        <div
            onClick={() => setAgentMenuOpen(true)}
            style={{
                cursor: 'pointer', margin: '0.5rem', padding: '0.8rem', font: '0.9rem', fontWeight: 600,
                borderRadius: 'var(--border-radius-md)', background: 'var(--bg-accent-secondary)',
                color: 'var(--color-text-primary)', boxShadow: 'var(--shadow-md)',
                display: 'flex', alignItems: 'center', marginBottom: '0.15rem',
                border: '1px solid var(--border-subtle)',
                flexDirection: 'row', width: '310px',
            }}
        >
            <span style={{ flex: 8 }} > Add Agents </span>
            <UserPlus style={{ flex: 1 }}  size={20} />
        </div>
    );

    const hidden = (
        <div
            className="glass-panel"
            style={{
                position: 'absolute', width: '320px', top: 20, right: 20,
                padding: '0.5rem', borderRadius: '5%', background: 'var(--bg-accent-secondary)',
                boxShadow: 'var(--shadow-md)', opacity: 0.7, zIndex: 10,
            }}
        >
            {toggleButton}
        </div>
    );

    const sliders = (
        <div style={{ flex: 1, overflowY: 'auto' }}>
            <h3 style={{
                fontSize: '0.75rem', textTransform: 'uppercase',
                letterSpacing: '0.05em', color: 'var(--color-text-muted)', marginBottom: '0.5rem',
            }}>
                Group {activeGroupId} Parameters
            </h3>

            <ParameterSlider
                label="Agent Count"
                icon={Users}
                value={config.agentCount}
                min={10} max={5000} step={10}
                onChange={(v) => handleChange('agentCount', v)}
            />
            <ParameterSlider
                label="Trust Decay"
                icon={TrendingDown}
                value={activeConfig?.trustDecay ?? config.trustDecay}
                min={0} max={1.0} step={0.01}
                onChange={(v) => handleGroupConfigChange('trustDecay', v)}
            />
            <ParameterSlider
                label="Trust Quota"
                icon={ShieldCheck}
                value={activeConfig?.trustQuota ?? config.trustQuota}
                min={0} max={1} step={0.05}
                onChange={(v) => handleGroupConfigChange('trustQuota', v)}
            />
            <ParameterSlider
                label="Simulation Speed"
                icon={Zap}
                value={activeConfig?.speedMultiplier ?? config.speedMultiplier}
                min={0.1} max={20.0} step={0.1}
                unit="x"
                onChange={(v) => handleGroupConfigChange('speedMultiplier', v)}
            />
            <ParameterSlider
                label="Good Trade Stickiness"
                icon={ShieldCheck}
                value={config.softSeparation}
                min={0.1} max={100.0} step={0.1}
                onChange={(v) => handleChange('softSeparation', v)}
            />
            <ParameterSlider
                label="Bad Trade Repulsion"
                icon={Activity}
                value={config.hardSeparation}
                min={1.0} max={100.0} step={0.5}
                onChange={(v) => handleChange('hardSeparation', v)}
            />
        </div>
    );

    const shown = (
        <aside
            className="glass-panel"
            style={{
                width: '320px', height: 'calc(100vh - 40px)', position: 'absolute',
                top: 20, right: 20, padding: '1rem', borderRadius: 'var(--radius-lg)',
                display: 'flex', flexDirection: 'column', zIndex: 10,
            }}
        >
            {toggleButton}

            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.25rem', color: 'var(--color-text-primary)' }}>
                Emergia Control
            </h2>
            <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                System Status: <span style={{ color: 'var(--color-success)' }}>ONLINE</span>
            </div>

            {/* Group Toggle */}
            <GroupToggle
                activeGroupId={activeGroupId}
                existingGroupIds={existingGroupIds}
                visibleGroupIds={visibleGroupIds}
                onSwitchGroup={switchGroup}
                // onToggleVisibility={toggleGroupVisibility}
                highlightedGroupId={highlightedGroupId}
                onToggleHighlight={(id) => setHighlightedGroupId(highlightedGroupId === id ? null : id)}
            />

            <div style={{ display: 'flex', flexDirection: 'row', marginBottom: '1rem' }}>
                {agentMenuOpen
                    ? <AgentMenu
                        onClose={() => setAgentMenuOpen(false)}
                        sendAction={sendAction}
                        activeGroupId={activeGroupId}
                        existingGroupIds={existingGroupIds}
                    />
                    : agentButton}
            </div>

            <ActionGroup
                isRunning={isRunning}
                onStart={handleStart}
                onPause={handlePause}
                onReset={handleReset}
            />

            {customAgentDisplayOpen
                ? <CustomAgentDisplay agents={agents} />
                : sliders}

            <div style={{
                marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)',
                fontSize: '0.75rem', color: 'var(--color-text-muted)', textAlign: 'center',
            }}>
                Emergia v0.1.0-alpha
            </div>
        </aside>
    );

    return maximized ? shown : hidden;
};