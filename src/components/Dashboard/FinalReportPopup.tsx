import React from 'react';
import { X, Activity, Users, ShieldCheck, TrendingUp, AlertTriangle } from 'lucide-react';

interface FinalReportPopupProps {
    report: {
        avgTrust: number;
        giniCoefficient: number;
        tradeSuccessRate: number;
        totalCollisions: number;
        tradeCount: number;
        [key: string]: any;
    };
    onClose: () => void;
}

export const FinalReportPopup: React.FC<FinalReportPopupProps> = ({ report, onClose }) => {
    if (!report) return null;

    console.log("FINAL REPORT RAW:", report);

    // Extract metrics safely handling potential nesting
    // Backend sends { global: { trust: { avg: ... }, giniCoefficient: { avg: ... }, ... } }
    const globalData = report.global || {};
    const trustData = globalData.trust || {};
    const giniData = globalData.giniCoefficient || {};

    const avgTrust = typeof trustData.avg === 'number' ? trustData.avg : (report.avgTrust ?? 0);
    const gini = typeof giniData.avg === 'number' ? giniData.avg : (report.giniCoefficient ?? 0);
    const successRate = globalData.tradeSuccessRate ?? report.tradeSuccessRate ?? 0;
    const totalCollisions = globalData.totalCollisions ?? report.totalCollisions ?? 0;
    const tradeCount = globalData.tradeCount ?? report.tradeCount ?? 0;

    return (
        <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(0,0,0,0.6)',
            backdropFilter: 'blur(4px)',
            zIndex: 50
        }}>
            <div className="glass-panel" style={{
                background: 'var(--bg-accent-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-xl)',
                padding: '2rem',
                width: '500px',
                maxWidth: '90%',
                boxShadow: 'var(--shadow-xl)',
                position: 'relative',
                animation: 'slideIn 0.3s ease-out'
            }}>
                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute',
                        top: '1rem',
                        right: '1rem',
                        background: 'none',
                        border: 'none',
                        color: 'var(--color-text-muted)',
                        cursor: 'pointer',
                        padding: '0.5rem',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}
                    onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--bg-accent-tertiary)'}
                    onMouseLeave={e => e.currentTarget.style.backgroundColor = 'none'}
                >
                    <X size={24} />
                </button>

                <h2 style={{
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    marginBottom: '1.5rem',
                    background: 'var(--gradient-text)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    textAlign: 'center'
                }}>
                    Simulation Report
                </h2>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <MetricCard
                        label="Average Trust"
                        value={avgTrust.toFixed(2)}
                        icon={<ShieldCheck size={20} />}
                        highlight={avgTrust > 0.7}
                    />
                    <MetricCard
                        label="Gini Coefficient"
                        value={gini.toFixed(2)}
                        icon={<TrendingUp size={20} />}
                        highlight={gini < 0.3}
                    />
                    <MetricCard
                        label="Success Rate"
                        value={`${(successRate * 100).toFixed(1)}%`}
                        icon={<Activity size={20} />}
                    />
                    <MetricCard
                        label="Total Trades"
                        value={tradeCount}
                        icon={<Users size={20} />}
                    />
                    <div style={{ gridColumn: 'span 2' }}>
                        <MetricCard
                            label="Total Collisions"
                            value={totalCollisions}
                            icon={<AlertTriangle size={20} />}
                        />
                    </div>
                </div>

                <div style={{
                    marginTop: '2rem',
                    textAlign: 'center',
                    fontSize: '0.875rem',
                    color: 'var(--color-text-muted)'
                }}>
                    Simulation ended successfully.
                </div>
            </div>
        </div>
    );
};

const MetricCard: React.FC<{ label: string; value: string | number; icon: React.ReactNode; highlight?: boolean }> = ({ label, value, icon, highlight }) => (
    <div style={{
        background: 'var(--bg-accent-secondary)',
        padding: '1rem',
        borderRadius: 'var(--radius-lg)',
        border: highlight ? '1px solid var(--color-success)' : '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center'
    }}>
        <div style={{ color: 'var(--color-accent-primary)', marginBottom: '0.5rem' }}>
            {icon}
        </div>
        <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {value}
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {label}
        </div>
    </div>
);
