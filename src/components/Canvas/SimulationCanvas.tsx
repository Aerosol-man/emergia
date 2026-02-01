import React, { useEffect, useRef } from 'react';
import { Renderer } from './Renderer';
import { useSimulationSocket } from '../../hooks/useSimulationSocket';
import { ControlPanel } from '../Controls/ControlPanel';
import { StatsOverlay } from '../Dashboard/StatsOverlay';
import { MetricsCharts } from '../Dashboard/MetricsCharts';

import { FinalReportPopup } from '../Dashboard/FinalReportPopup';

const SimulationCanvas: React.FC = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const rendererRef = useRef<Renderer | null>(null);

    const {
        stateBuffer,
        isConnected,
        sendAction,
        lastMetrics,
        agents,
        activeGroupId,
        existingGroupIds,
        groupConfigs,
        visibleGroupIds,
        switchGroup,
        updateGroupConfig,
        toggleGroupVisibility,
        finalReport,
        setFinalReport,
    } = useSimulationSocket();

    useEffect(() => {
        if (finalReport) {
            console.log("CANVAS RECEIVED FINAL REPORT:", finalReport);
        }
    }, [finalReport]);

    useEffect(() => {
        if (!containerRef.current || !canvasRef.current) return;

        const { clientWidth, clientHeight } = containerRef.current;
        rendererRef.current = new Renderer(canvasRef.current, clientWidth, clientHeight, stateBuffer);
        rendererRef.current.start();

        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                if (entry.target === containerRef.current && rendererRef.current) {
                    const { width, height } = entry.contentRect;
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

            <div style={{ position: 'absolute', top: 20, left: 20, color: isConnected ? '#22c55e' : '#ef4444', fontFamily: 'monospace', zIndex: 5, pointerEvents: 'none' }}>
                ● {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
            </div>

            <ControlPanel
                sendAction={sendAction}
                agents={agents}
                activeGroupId={activeGroupId}
                existingGroupIds={existingGroupIds}
                groupConfigs={groupConfigs}
                visibleGroupIds={visibleGroupIds}
                switchGroup={switchGroup}
                updateGroupConfig={updateGroupConfig}
                toggleGroupVisibility={toggleGroupVisibility}
            />

            <MetricsCharts metrics={lastMetrics} />
            <StatsOverlay metrics={lastMetrics} />

            {finalReport && (
                <FinalReportPopup
                    report={finalReport}
                    onClose={() => setFinalReport(null)}
                />
            )}
        </div>
    );
};

export default SimulationCanvas;