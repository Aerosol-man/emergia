import React, { useState } from 'react';
import { Activity, BarChart3, Globe2, Scale, Info, EyeOff } from 'lucide-react';
import type { SimulationState } from '../../types/simulation';

interface StatsOverlayProps {
    metrics: SimulationState['metrics'] | null;
}

export const StatsOverlay: React.FC<StatsOverlayProps> = ({ metrics }) => {
    if (!metrics) return null;

    const [activePopup, setActivePopup] = useState<string | null>(null);
    const [showStats, setShowStats] = useState(true);

    const InfoCard = ({ title, text, onClose }: { title: string, text: string, onClose: () => void }) => (
        <div style={{
            position: 'absolute',
            bottom: '120%',
            left: '50%',
            transform: 'translateX(-50%)',
            width: '240px',
            padding: '1rem',
            background: 'var(--color-bg-primary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3)',
            color: 'var(--color-text-primary)',
            zIndex: 30,
            cursor: 'default'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                    {title}
                </h4>
                <button
                    onClick={(e) => { e.stopPropagation(); onClose(); }}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: 'var(--color-text-muted)' }}
                >
                    &times;
                </button>
            </div>
            <p style={{ fontSize: '0.8rem', lineHeight: '1.4', color: 'var(--color-text-secondary)', margin: 0 }}>
                {text}
            </p>

            {/* Arrow */}
            <div style={{
                position: 'absolute',
                top: '100%',
                left: '50%',
                transform: 'translateX(-50%)',
                borderLeft: '8px solid transparent',
                borderRight: '8px solid transparent',
                borderTop: '8px solid var(--color-bg-primary)'
            }} />
        </div>
    );

    const StatItem: React.FC<{ label: string; value: string; icon: React.ElementType; color: string; info: string }> = ({ label, value, icon: Icon, color, info }) => {
        const isOpen = activePopup === label;

        return (
            <div
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '0 1.5rem', position: 'relative' }}
            >
                {isOpen && <InfoCard title={label} text={info} onClose={() => setActivePopup(null)} />}

                <div
                    style={{ display: 'flex', alignItems: 'center', marginBottom: '0.25rem', color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', cursor: 'pointer' }}
                    onClick={() => setActivePopup(isOpen ? null : label)}
                >
                    <Icon size={14} style={{ marginRight: '0.4rem', color }} />
                    {label}
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '18px',
                        height: '18px',
                        borderRadius: '50%',
                        background: isOpen ? 'var(--color-accent-primary)' : 'rgba(255,255,255,0.1)',
                        color: isOpen ? 'white' : 'inherit',
                        marginLeft: '0.5rem',
                        transition: 'all 0.2s'
                    }}>
                        <Info size={12} style={{ opacity: isOpen ? 1 : 0.8 }} />
                    </div>
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--color-text-primary)' }}>
                    {value}
                </div>
            </div>
        );
    };

    const toggleButton = (
        <div
            onClick={() => setShowStats(!showStats)}
            style={{ cursor: 'pointer', padding: '0.5rem', borderRadius: '50%', background: 'var(--bg-accent-secondary)', boxShadow: 'var(--shadow-md)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {showStats ? <EyeOff size={20} style={{ color: 'var(--color-text-primary)' }} /> : <BarChart3 size={20} style={{ color: 'var(--color-text-primary)' }} />}
        </div>
    )

    const buttonStyle = {
        position: 'absolute',
        bottom: 30,
        left: '50%',
        transform: 'translateX(-50%)',
        padding: '1rem 2rem',
        borderRadius: 'var(--radius-lg)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10,
        opacity: 0.7,
        transition: 'opacity 0.3s',
        pointerEvents: 'auto' as 'auto',
        ...(showStats ? { opacity: 1 } : {}),
        '&:hover': { opacity: 1 }
    }

    const hidden = (
        <div className="glass-panel" style={buttonStyle}>
            {toggleButton}
        </div>
    )

    const shown = (
        <div className="glass-panel" style={{
            position: 'absolute',
            bottom: 30,
            left: '50%',
            transform: 'translateX(-50%)',
            padding: '1rem 2rem',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10
        }}>
            {toggleButton}

            <div style={{ width: '1px', height: '30px', background: 'var(--border-subtle)', margin: '0 1rem' }} />

            <StatItem
                label="Avg Trust"
                value={metrics.avgTrust.toFixed(2)}
                icon={Globe2}
                color="var(--color-success)"
                info="Global average trust level (0.0 - 1.0). Higher means more cooperation."
            />

            <div style={{ width: '1px', height: '30px', background: 'var(--border-subtle)', margin: '0 1rem' }} />

            <StatItem
                label="Inequality (Gini)"
                value={metrics.giniCoefficient.toFixed(3)}
                icon={Scale}
                color="var(--color-warning)"
                info="Gini coefficient of trust. 0 = equality, 1 = max inequality."
            />

            <div style={{ width: '1px', height: '30px', background: 'var(--border-subtle)', margin: '0 1rem' }} />

            <StatItem
                label="Trade Success"
                value={`${(metrics.tradeSuccessRate * 100).toFixed(0)}%`}
                icon={BarChart3}
                color="var(--color-accent-primary)"
                info="Percentage of interactions resulting in successful trades."
            />

            <div style={{ width: '1px', height: '30px', background: 'var(--border-subtle)', margin: '0 1rem' }} />

            <StatItem
                label="Tick Rate"
                value="30Hz"
                icon={Activity}
                color="var(--color-text-muted)"
                info="Simulation update frequency."
            />
        </div>
    );

    return showStats ? shown : hidden;
};
