import React from 'react';
import { Activity, BarChart3, Globe2, Scale } from 'lucide-react';
import type { SimulationState } from '../../types/simulation';

interface StatsOverlayProps {
    metrics: SimulationState['metrics'] | null;
}

export const StatsOverlay: React.FC<StatsOverlayProps> = ({ metrics }) => {
    if (!metrics) return null;

    const StatItem: React.FC<{ label: string; value: string; icon: React.ElementType; color: string }> = ({ label, value, icon: Icon, color }) => (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '0 1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.25rem', color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <Icon size={14} style={{ marginRight: '0.4rem', color }} />
                {label}
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--color-text-primary)' }}>
                {value}
            </div>
        </div>
    );

    return (
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
            <StatItem
                label="Avg Trust"
                value={metrics.avgTrust.toFixed(2)}
                icon={Globe2}
                color="var(--color-success)"
            />

            <div style={{ width: '1px', height: '30px', background: 'var(--border-subtle)', margin: '0 1rem' }} />

            <StatItem
                label="Inequality (Gini)"
                value={metrics.giniCoefficient.toFixed(3)}
                icon={Scale}
                color="var(--color-warning)"
            />

            <div style={{ width: '1px', height: '30px', background: 'var(--border-subtle)', margin: '0 1rem' }} />

            <StatItem
                label="Trade Success"
                value={`${(metrics.tradeSuccessRate * 100).toFixed(0)}%`}
                icon={BarChart3}
                color="var(--color-accent-primary)"
            />

            <div style={{ width: '1px', height: '30px', background: 'var(--border-subtle)', margin: '0 1rem' }} />

            <StatItem
                label="Tick Rate"
                value="30Hz"
                icon={Activity}
                color="var(--color-text-muted)"
            />
        </div>
    );
};
