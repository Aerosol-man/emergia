import React, { useState } from 'react';
import { ParameterSlider } from './ParameterSlider';
import { ActionGroup } from './ActionGroup';
import { Users, TrendingDown, ShieldCheck, Zap } from 'lucide-react';
import type { ClientAction, SimulationConfig } from '../../types/simulation';

interface ControlPanelProps {
    sendAction: (action: ClientAction) => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({ sendAction }) => {
    // Local state for UI responsiveness before sending to socket
    const [config, setConfig] = useState<SimulationConfig>({
        agentCount: 500,
        trustDecay: 0.05,
        trustQuota: 0.3,
        speedMultiplier: 1.0
    });

    // Simple debouncer could go here, but for now we send updates directly
    // Ideally use useDebounce or similar if high traffic

    const handleChange = (key: keyof SimulationConfig, value: number) => {
        const newConfig = { ...config, [key]: value };
        setConfig(newConfig);
        sendAction({ type: 'update_config', payload: { [key]: value } });
    };

    const [isRunning, setIsRunning] = useState(true);

    const handleStart = () => {
        setIsRunning(true);
        sendAction({ type: 'start' });
    };

    const handlePause = () => {
        setIsRunning(false);
        sendAction({ type: 'pause' });
    };

    const handleReset = () => {
        sendAction({ type: 'reset' });
    };

    return (
        <aside className="glass-panel" style={{
            width: '320px',
            height: 'calc(100vh - 40px)',
            position: 'absolute',
            top: 20,
            right: 20,
            padding: '1.5rem',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 10
        }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.25rem', color: 'var(--color-text-primary)' }}>
                Emergia Control
            </h2>
            <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '2rem' }}>
                System Status: <span style={{ color: 'var(--color-success)' }}>ONLINE</span>
            </div>

            <ActionGroup
                isRunning={isRunning}
                onStart={handleStart}
                onPause={handlePause}
                onReset={handleReset}
            />

            <div style={{ flex: 1, overflowY: 'auto' }}>
                <h3 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                    Parameters
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
                    value={config.trustDecay}
                    min={0} max={0.2} step={0.001}
                    onChange={(v) => handleChange('trustDecay', v)}
                />

                <ParameterSlider
                    label="Trust Quota"
                    icon={ShieldCheck}
                    value={config.trustQuota}
                    min={0} max={1} step={0.05}
                    onChange={(v) => handleChange('trustQuota', v)}
                />

                <ParameterSlider
                    label="Sim Speed"
                    icon={Zap}
                    value={config.speedMultiplier}
                    min={0.1} max={5.0} step={0.1} unit="x"
                    onChange={(v) => handleChange('speedMultiplier', v)}
                />
            </div>

            <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)', fontSize: '0.75rem', color: 'var(--color-text-muted)', textAlign: 'center' }}>
                Emergia v0.1.0-alpha
            </div>
        </aside>
    );
};
