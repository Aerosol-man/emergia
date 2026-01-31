import React, { useEffect, useRef, useState } from 'react';
import { scaleLinear } from 'd3-scale';
import { Globe2, Scale, BarChart3, ChevronDown, ChevronUp } from 'lucide-react';
import type { SimulationState } from '../../types/simulation';

interface MetricsChartsProps {
    metrics: SimulationState['metrics'] | null;
}

// Keep last N data points
const HISTORY_LENGTH = 100;

interface MetricsData {
    avgTrust: number;
    giniCoefficient: number;
    tradeSuccessRate: number;
}

interface MetricHistoryPoint extends MetricsData {
    tick: number;
}

export const MetricsCharts: React.FC<MetricsChartsProps> = ({ metrics }) => {
    // History buffer
    const historyRef = useRef<MetricHistoryPoint[]>([]);
    // Trigger re-render
    const [, setTick] = useState(0);
    // Collapse state
    const [isCollapsed, setIsCollapsed] = useState(false);

    useEffect(() => {
        if (!metrics) return;

        // Add new point
        historyRef.current.push({
            tick: Date.now(), // Using timestamp for simple scrolling x-axis or just index
            avgTrust: metrics.avgTrust,
            giniCoefficient: metrics.giniCoefficient,
            tradeSuccessRate: metrics.tradeSuccessRate
        });

        // Prune
        if (historyRef.current.length > HISTORY_LENGTH) {
            historyRef.current.shift();
        }

        setTick(t => t + 1);
    }, [metrics]);

    if (!metrics && historyRef.current.length === 0) return null;

    // Dimensions
    const width = 280;
    const height = 80; // Increased height for better visibility
    const padding = { top: 10, right: 10, bottom: 10, left: 35 }; // More left padding for axis
    const innerWidth = width - padding.left - padding.right;
    const innerHeight = height - padding.top - padding.bottom;

    // Scales
    // X is always 0 to HISTORY_LENGTH-1
    const xScale = scaleLinear()
        .domain([0, HISTORY_LENGTH - 1])
        .range([0, innerWidth]);

    // Y Scale: Fixed 0 to 1 for these normalized metrics
    const yScale = scaleLinear()
        .domain([0, 1])
        .range([innerHeight, 0]);

    // Helpers to generate path data
    const generatePath = (getValue: (d: MetricsData) => number) => {
        const data = historyRef.current;
        if (data.length < 2) return '';

        let pathD = `M ${xScale(0)} ${yScale(getValue(data[0]))}`;

        for (let i = 1; i < data.length; i++) {
            pathD += ` L ${xScale(i)} ${yScale(getValue(data[i]))}`;
        }
        return pathD;
    };

    const ChartRow = ({ label, icon: Icon, color, getValue, formatValue }: { label: string, icon: any, color: string, getValue: (d: MetricsData) => number, formatValue: (v: number) => string }) => {
        const currentValue = metrics ? getValue(metrics) : (historyRef.current.length > 0 ? getValue(historyRef.current[historyRef.current.length - 1]) : 0);

        return (
            <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem', paddingLeft: padding.left }}>
                    <div style={{ display: 'flex', alignItems: 'center', fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        <Icon size={12} style={{ marginRight: '0.4rem', color: color }} />
                        {label}
                    </div>
                    <div style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                        {formatValue(currentValue)}
                    </div>
                </div>

                <div style={{ position: 'relative', width: width, height: height, background: 'rgba(0,0,0,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                    <svg width={width} height={height} style={{ display: 'block' }}>
                        <g transform={`translate(${padding.left}, ${padding.top})`}>
                            {/* Grid Lines & Axis Labels */}
                            {[0, 0.5, 1.0].map(tick => (
                                <g key={tick} transform={`translate(0, ${yScale(tick)})`}>
                                    <line x1={0} y1={0} x2={innerWidth} y2={0} stroke="var(--border-subtle)" strokeOpacity={0.5} strokeDasharray="4 4" />
                                    <text x={-5} y={4} textAnchor="end" fontSize="9" fill="var(--color-text-muted)" style={{ fontFamily: 'var(--font-mono)' }}>
                                        {tick.toFixed(1)}
                                    </text>
                                </g>
                            ))}

                            {/* Data Line */}
                            <path
                                d={generatePath(getValue)}
                                fill="none"
                                stroke={color}
                                strokeWidth={2}
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                        </g>
                    </svg>
                </div>
            </div>
        );
    };

    return (
        <aside className="glass-panel" style={{
            position: 'absolute',
            top: 20,
            left: 20,
            padding: '1.5rem',
            borderRadius: 'var(--radius-lg)',
            zIndex: 10,
            width: width + 48 // padding similar to container
        }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: isCollapsed ? 0 : '1rem' }}>
                <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-primary)', margin: 0 }}>
                    Live Metrics
                </h3>
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--color-text-muted)',
                        cursor: 'pointer',
                        padding: 0,
                        display: 'flex',
                        transition: 'color 0.2s'
                    }}
                    onMouseEnter={e => e.currentTarget.style.color = 'var(--color-text-primary)'}
                    onMouseLeave={e => e.currentTarget.style.color = 'var(--color-text-muted)'}
                >
                    {isCollapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
                </button>
            </div>

            {!isCollapsed && (
                <>
                    <ChartRow
                        label="Avg Trust"
                        icon={Globe2}
                        color="var(--color-success)"
                        getValue={d => d.avgTrust}
                        formatValue={v => v.toFixed(2)}
                    />
                    <ChartRow
                        label="Inequality"
                        icon={Scale}
                        color="var(--color-warning)"
                        getValue={d => d.giniCoefficient}
                        formatValue={v => v.toFixed(3)}
                    />
                    <ChartRow
                        label="Trade Success"
                        icon={BarChart3}
                        color="var(--color-accent-primary)"
                        getValue={d => d.tradeSuccessRate}
                        formatValue={v => `${(v * 100).toFixed(0)}%`}
                    />
                </>
            )}
        </aside>
    );
};
