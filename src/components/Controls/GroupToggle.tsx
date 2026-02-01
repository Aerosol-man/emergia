import React from 'react';

const MAX_GROUPS = 5;

interface GroupToggleProps {
    activeGroupId: number;
    existingGroupIds: number[];
    onSwitchGroup: (groupId: number) => void;
}

export const GroupToggle: React.FC<GroupToggleProps> = ({
    activeGroupId,
    existingGroupIds,
    onSwitchGroup,
}) => {
    const groupIds = Array.from({ length: MAX_GROUPS }, (_, i) => i);

    return (
        <div style={{
            display: 'flex',
            gap: '0.25rem',
            padding: '0.25rem',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: 'var(--radius-md, 8px)',
            border: '1px solid var(--border-subtle, rgba(255,255,255,0.1))',
            marginBottom: '0.75rem',
        }}>
            {groupIds.map((gid) => {
                const exists = existingGroupIds.includes(gid);
                const isActive = gid === activeGroupId;

                return (
                    <button
                        key={gid}
                        onClick={() => {
                            if (exists) onSwitchGroup(gid);
                        }}
                        disabled={!exists}
                        style={{
                            flex: 1,
                            padding: '0.4rem 0.5rem',
                            border: 'none',
                            borderRadius: 'var(--radius-sm, 6px)',
                            cursor: exists ? 'pointer' : 'default',
                            fontSize: '0.75rem',
                            fontWeight: isActive ? 700 : 500,
                            transition: 'all 0.15s ease',
                            background: isActive
                                ? 'var(--color-accent-primary, #6366f1)'
                                : exists
                                    ? 'rgba(255, 255, 255, 0.08)'
                                    : 'transparent',
                            color: isActive
                                ? '#fff'
                                : exists
                                    ? 'var(--color-text-secondary, #aaa)'
                                    : 'var(--color-text-muted, #555)',
                            opacity: exists ? 1 : 0.3,
                        }}
                        title={exists ? `Switch to Group ${gid}` : `Group ${gid} — not created`}
                    >
                        G{gid}
                    </button>
                );
            })}
        </div>
    );
};