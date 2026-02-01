import React, { useState } from 'react';
import { ParameterSlider } from './ParameterSlider';
import { ActionGroup } from './ActionGroup';
import { Users, TrendingDown, ShieldCheck, ChevronDown, ChevronUp, Zap, UserPlus, Activity } from 'lucide-react';
import { AgentMenu } from './AgentMenu'
import type { ClientAction, SimulationConfig } from '../../types/simulation';

interface ControlPanelProps {
    sendAction: (action: ClientAction) => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({ sendAction }) => {
    const [config, setConfig] = useState<SimulationConfig>({
        agentCount: 500,
        trustDecay: 0.05,
        trustQuota: 0.3,
        speedMultiplier: 1.0,

        // 🔥 NEW — social physics controls
        softSeparation: 0.8,
        hardSeparation: 6.0
    });

    const [isRunning, setIsRunning] = useState(false);
    const [maximized, setMaximized] = useState(true);
    const [agentMenuOpen, setAgentMenuOpen] = useState(false);

    const handleChange = (key: keyof SimulationConfig, value: number) => {
        const newConfig = { ...config, [key]: value };
        setConfig(newConfig);

        sendAction({
            type: 'update_config',
            payload: { [key]: value }
        });
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
                cursor: 'pointer',
                padding: '0.5rem',
                borderRadius: '50%', 
                background: 'var(--bg-accent-secondary)',
                boxShadow: 'var(--shadow-md)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flex: 0.25
        }}>
            {maximized ? <ChevronUp size={20} style={{ color: 'var(--color-text-primary)' }} /> : <ChevronDown size={20} style={{ color: 'var(--color-text-primary)' }} />}
        </div>
    );

    const agentButton = (
        <div
            onClick={() => setAgentMenuOpen(true)}
            style={{ cursor: 'pointer', flex: .3, margin: '0.5rem', padding: '0.5rem', borderRadius: '5%', background: 'var(--bg-accent-secondary)', boxShadow: 'var(--shadow-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.5rem' }}>
            <UserPlus size={20} style={{ color: 'var(--color-text-primary)' }} />
        </div>
    );

    const hidden = (
        <div
            className="glass-panel"
            style={{
                position: 'absolute',
                width: '320px',
                top: 20,
                right: 20,
                padding: '0.5rem',
                borderRadius: '5%',
                background: 'var(--bg-accent-secondary)',
                boxShadow: 'var(--shadow-md)',
                opacity: 0.7,
                zIndex: 10
            }}
        >
            {toggleButton}
        </div>
    );

    const shown = (
        <aside
            className="glass-panel"
            style={{
                width: '320px',
                height: 'calc(100vh - 40px)',
                position: 'absolute',
                top: 20,
                right: 20,
                padding: '1rem',
                borderRadius: 'var(--radius-lg)',
                display: 'flex',
                flexDirection: 'column',
                zIndex: 10
            }}
        >
            {toggleButton}

            <h2
                style={{
                    fontSize: '1.25rem',
                    fontWeight: 700,
                    marginBottom: '0.25rem',
                    color: 'var(--color-text-primary)'
                }}
            >
                Emergia Control
            </h2>

            <div
                style={{
                    fontSize: '0.85rem',
                    color: 'var(--color-text-muted)',
                    marginBottom: '2rem'
                }}
            >
                System Status:{' '}
                <span style={{ color: 'var(--color-success)' }}>ONLINE</span>
            </div>

            <div
                style={{
                    display: 'flex',
                    flexDirection: 'row',
                    marginBottom: '1rem',
                }}
            >
                <div style={{ flex: 1, border: '1px solid var(--border-subtle)', borderRadius: '5%', display: 'flex', alignItems: 'center', fontSize: '0.9rem', fontWeight: 500, color: 'var(--color-text-primary)', flexDirection: 'row' }}>
                    <Users size={16} style={{ marginRight: '0.5rem', color: 'var(--color-accent-primary)', flex: 1 }} />
                    <div style={{flex: 2, padding: '0.5rem'}} >My Agents</div>
                </div>
                { agentMenuOpen ? <AgentMenu onClose={() => setAgentMenuOpen(false)} /> : agentButton }
            </div>

            <ActionGroup
                isRunning={isRunning}
                onStart={handleStart}
                onPause={handlePause}
                onReset={handleReset}
            />

            <div style={{ flex: 1, overflowY: 'auto' }}>
                <h3
                    style={{
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        color: 'var(--color-text-muted)',
                        marginBottom: '1rem'
                    }}
                >
                    Parameters
                </h3>

                <ParameterSlider
                    label="Agent Count"
                    icon={Users}
                    value={config.agentCount}
                    min={10}
                    max={5000}
                    step={10}
                    onChange={(v) => handleChange('agentCount', v)}
                />

                <ParameterSlider
                    label="Trust Decay"
                    icon={TrendingDown}
                    value={config.trustDecay}
                    min={0}
                    max={0.2}
                    step={0.001}
                    onChange={(v) => handleChange('trustDecay', v)}
                />

                <ParameterSlider
                    label="Trust Quota"
                    icon={ShieldCheck}
                    value={config.trustQuota}
                    min={0}
                    max={1}
                    step={0.05}
                    onChange={(v) => handleChange('trustQuota', v)}
                />

                <ParameterSlider
                    label="Simulation Speed"
                    icon={Zap}
                    value={config.speedMultiplier}
                    min={0.1}
                    max={5.0}
                    step={0.1}
                    unit="x"
                    onChange={(v) => handleChange('speedMultiplier', v)}
                />

                {/* 🔥 NEW — SOCIAL PHYSICS CONTROLS */}

                <ParameterSlider
                    label="Good Trade Stickiness"
                    icon={ShieldCheck}
                    value={config.softSeparation}
                    min={0.1}
                    max={3.0}
                    step={0.1}
                    onChange={(v) => handleChange('softSeparation', v)}
                />

                <ParameterSlider
                    label="Bad Trade Repulsion"
                    icon={Activity}
                    value={config.hardSeparation}
                    min={1.0}
                    max={12.0}
                    step={0.5}
                    onChange={(v) => handleChange('hardSeparation', v)}
                />
            </div>

            <div
                style={{
                    marginTop: 'auto',
                    paddingTop: '1rem',
                    borderTop: '1px solid var(--border-subtle)',
                    fontSize: '0.75rem',
                    color: 'var(--color-text-muted)',
                    textAlign: 'center'
                }}
            >
                Emergia v0.1.0-alpha
            </div>
        </aside>
    );

    return maximized ? shown : hidden;
};
