import React from 'react';
import { Users } from 'lucide-react';

export const CustomAgentDisplay: React.FC = () => {
    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            padding: '0.5rem',
        }}>
            <Users size={20} style={{ marginRight: '0.5rem', color: 'var(--color-accent-primary)' }} />
            <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>My Agents</span>
        </div>
    );
}

