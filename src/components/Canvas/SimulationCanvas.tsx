import React, { useEffect, useRef } from 'react';
import { Renderer } from './Renderer';
import { useSimulationSocket } from '../../hooks/useSimulationSocket';
import { ControlPanel } from '../Controls/ControlPanel';
import { StatsOverlay } from '../Dashboard/StatsOverlay';
import { MetricsCharts } from '../Dashboard/MetricsCharts';

const SimulationCanvas: React.FC = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const rendererRef = useRef<Renderer | null>(null);

    const { stateBuffer, isConnected, sendAction, lastMetrics } = useSimulationSocket();

    useEffect(() => {
        if (!containerRef.current || !canvasRef.current) return;

        // init renderer
        const { clientWidth, clientHeight } = containerRef.current;
        rendererRef.current = new Renderer(canvasRef.current, clientWidth, clientHeight, stateBuffer);
        rendererRef.current.start();

        // handle resize using ResizeObserver
        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                if (entry.target === containerRef.current && rendererRef.current) {
                    const { width, height } = entry.contentRect;
                    // Ensure we don't resize to 0 causing issues
                    if (width > 0 && height > 0) {
                        rendererRef.current.resize(width, height);
                    }
                }
            }
        });

        resizeObserver.observe(containerRef.current);

        return () => {
            rendererRef.current?.stop();
            resizeObserver.disconnect();
        };
    }, []);

    return (
        <div ref={containerRef} style={{ width: '100%', height: '100vh', position: 'relative', overflow: 'hidden' }}>
            <canvas ref={canvasRef} style={{ display: 'block' }} />

            {/* Status Indicator */}
            <div style={{ position: 'absolute', top: 20, left: 20, color: isConnected ? '#22c55e' : '#ef4444', fontFamily: 'monospace', zIndex: 5, pointerEvents: 'none' }}>
                ● {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
            </div>

            {/* Controls */}
            <ControlPanel sendAction={sendAction} />

            {/* Metrics Charts (Top Left) */}
            <MetricsCharts metrics={lastMetrics} />

            {/* Dashboard Stats */}
            <StatsOverlay metrics={lastMetrics} />
        </div>
    );
};

export default SimulationCanvas;
