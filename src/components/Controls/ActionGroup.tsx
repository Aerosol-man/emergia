import React from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';

interface ActionGroupProps {
    onStart: () => void;
    onPause: () => void;
    onReset: () => void;
    isRunning: boolean;
}

export const ActionGroup: React.FC<ActionGroupProps> = ({ onStart, onPause, onReset, isRunning }) => {
    const btnStyle: React.CSSProperties = {
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0.75rem',
        borderRadius: 'var(--radius-md)',
        border: 'none',
        cursor: 'pointer',
        fontWeight: 600,
        transition: 'all 0.2s',
        gap: '0.5rem'
    };

    return (
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
            {isRunning ? (
                <button
                    onClick={onPause}
                    style={{ ...btnStyle, background: 'rgba(239, 68, 68, 0.2)', color: 'var(--color-danger)', border: '1px solid rgba(239, 68, 68, 0.5)' }}
                >
                    <Pause size={18} /> Pause
                </button>
            ) : (
                <button
                    onClick={onStart}
                    style={{ ...btnStyle, background: 'rgba(34, 197, 94, 0.2)', color: 'var(--color-success)', border: '1px solid rgba(34, 197, 94, 0.5)' }}
                >
                    <Play size={18} /> Start
                </button>
            )}

            <button
                onClick={onReset}
                style={{ ...btnStyle, flex: 0, padding: '0.75rem', background: 'var(--color-bg-tertiary)', color: 'var(--color-text-secondary)' }}
                title="Reset Simulation"
            >
                <RotateCcw size={18} />
            </button>
        </div>
    );
};
