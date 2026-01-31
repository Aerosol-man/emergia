import React, { useEffect, useRef } from 'react';
import { Renderer } from './Renderer';
import { useSimulationSocket } from '../../hooks/useSimulationSocket';
import { ControlPanel } from '../Controls/ControlPanel';
import { StatsOverlay } from '../Dashboard/StatsOverlay';

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

        // handle resize
        const handleResize = () => {
            if (containerRef.current && rendererRef.current) {
                const { clientWidth, clientHeight } = containerRef.current;
                rendererRef.current.resize(clientWidth, clientHeight);
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            rendererRef.current?.stop();
            window.removeEventListener('resize', handleResize);
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

            {/* Dashboard Stats */}
            <StatsOverlay metrics={lastMetrics} />
        </div>
    );
};

export default SimulationCanvas;
