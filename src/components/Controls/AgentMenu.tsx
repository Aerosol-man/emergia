import React from 'react';
import { ParameterSlider } from './ParameterSlider'
import { Menu, Scale, TrendingDown, TrendingUp, UserPlus } from 'lucide-react';

interface AgentMenuProps {
    onClose: () => void;
}

export const AgentMenu: React.FC<AgentMenuProps> = ({ onClose }) => {
    const [trustQuota, setTrustQuota] = React.useState(0.3);
    const [trustGain, setTrustGain] = React.useState(0.3);
    const [trustLoss, setTrustLoss] = React.useState(0.3);

    return (
        <div className="glass-panel"
            style={{
                position: 'absolute',
                top: 20,
                right: 340,
                height: 'calc(55vh - 40px)',
                width: '200px',
                padding: '1rem',
                borderRadius: 'var(--radius-lg)',
                zIndex: 20,
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem'
            }}
        >
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
                <UserPlus size={20} style={{ marginRight: '0.5rem', color: 'var(--color-accent-primary)' }} />
                <span style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Agent Menu</span>
                <div
                    onClick={onClose}
                    style={{ marginLeft: 'auto', cursor: 'pointer', fontSize: '1.2rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}
                    
                >
                    &times;
                </div>
            </div>

            <ParameterSlider
                label='Trust Quota'
                icon={Scale}
                onChange={(q) => setTrustQuota(q)}
                value={trustQuota}
                min={0} max={1} step={0.05}
            />

            <ParameterSlider
                label='Transaction Success Gain'
                icon={TrendingUp}
                onChange={(q) => setTrustGain(q)}
                value={trustGain}
                min={0} max={1} step={0.05}
            />

            <ParameterSlider
                label='Transaction Failure Loss'
                icon={TrendingDown}
                onChange={(q) => setTrustLoss(q)}
                value={trustLoss}
                min={0} max={1} step={0.05}
            />

            <button
                style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '0.25rem',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    fontWeight: 600,
                    transition: 'all 0.2s',
                    gap: '0.5rem',
                    background: 'rgba(34, 197, 94, 0.2)',
                    color: 'var(--color-success)',
                    border: '1px solid rgba(34, 197, 94, 0.5)'
                }} >
                <UserPlus size={18} /> Add Agent
            </button>
        </div>
    );
}