import React from 'react';

interface CustomAgentDisplayProps {
    agents: any[];
}

export const CustomAgentDisplay: React.FC<CustomAgentDisplayProps> = ({ agents = [] }) => {
    // Debug: Log agents to see if we're receiving them and if isCustom is present
    const customAgents = agents.filter(a => {
        // console.log('Checking agent:', a.id, 'isCustom:', a.isCustom);
        return a.isCustom;
    });

    console.log(`CustomAgentDisplay rendering. Total agents: ${agents.length}, Custom: ${customAgents.length}`);

    return (
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {customAgents.length === 0 ? (
                <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
                    No custom agents yet. Add one!
                </div>
            ) : (
                customAgents.map(agent => (
                    <div key={agent.id} style={{
                        padding: '0.75rem',
                        borderRadius: 'var(--radius-md)',
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '0.8rem'
                    }}>
                        <div style={{ fontWeight: 600, marginBottom: '0.25rem', color: 'var(--color-accent-primary)' }}>
                            Agent #{agent.id}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.25rem', color: 'var(--color-text-secondary)' }}>
                            <div>Trust: {(agent.trust || 0).toFixed(2)}</div>
                            <div>Quota: {agent.trustQuota?.toFixed(2)}</div>
                            <div>Trades: {agent.tradeCount}</div>
                        </div>
                    </div>
                ))
            )}
        </div>
    );
}

