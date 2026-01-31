import React from 'react';
import type { ChangeEvent } from 'react';
import type { LucideIcon } from 'lucide-react';

interface ParameterSliderProps {
    label: string;
    icon: LucideIcon;
    value: number;
    min: number;
    max: number;
    step?: number;
    onChange: (val: number) => void;
    unit?: string;
}

export const ParameterSlider: React.FC<ParameterSliderProps> = ({
    label,
    icon: Icon,
    value,
    min,
    max,
    step = 0.1,
    onChange,
    unit = ''
}) => {
    return (
        <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem', color: 'var(--color-text-secondary)' }}>
                <Icon size={16} style={{ marginRight: '0.5rem' }} />
                <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{label}</span>
                <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--color-accent-primary)' }}>
                    {value.toFixed(1)}{unit}
                </span>
            </div>

            <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(parseFloat(e.target.value))}
                style={{
                    width: '100%',
                    height: '6px',
                    borderRadius: '3px',
                    background: 'var(--color-bg-tertiary)',
                    accentColor: 'var(--color-accent-primary)',
                    cursor: 'pointer',
                    outline: 'none'
                }}
            />
        </div>
    );
};
