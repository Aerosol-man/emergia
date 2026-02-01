import React from 'react';
import { Eye, EyeOff } from 'lucide-react';

const MAX_GROUPS = 5;

interface GroupToggleProps {
    activeGroupId: number;
    existingGroupIds: number[];
    visibleGroupIds: Set<number>;
    onSwitchGroup: (groupId: number) => void;
    onToggleVisibility: (groupId: number) => void;
}

export const GroupToggle: React.FC<GroupToggleProps> = ({
    activeGroupId,
    existingGroupIds,
    visibleGroupIds,
    onSwitchGroup,
    onToggleVisibility,
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
                const isVisible = visibleGroupIds.has(gid);

                return (
                    <div
                        key={gid}
                        style={{
                            flex: 1,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.15rem',
                            borderRadius: 'var(--radius-sm, 6px)',
                            background: isActive
                                ? 'var(--color-accent-primary, #6366f1)'
                                : exists
                                    ? 'rgba(255, 255, 255, 0.08)'
                                    : 'transparent',
                            opacity: exists ? 1 : 0.3,
                            transition: 'all 0.15s ease',
                            overflow: 'hidden',
                        }}
                    >
                        {/* Group select button */}
                        <button
                            onClick={() => {
                                if (exists) onSwitchGroup(gid);
                            }}
                            disabled={!exists}
                            style={{
                                flex: 1,
                                padding: '0.4rem 0.3rem',
                                border: 'none',
                                background: 'transparent',
                                cursor: exists ? 'pointer' : 'default',
                                fontSize: '0.75rem',
                                fontWeight: isActive ? 700 : 500,
                                color: isActive
                                    ? '#fff'
                                    : exists
                                        ? 'var(--color-text-secondary, #aaa)'
                                        : 'var(--color-text-muted, #555)',
                            }}
                            title={exists ? `Switch to Group ${gid}` : `Group ${gid} — not created`}
                        >
                            G{gid}
                        </button>

                        {/* Visibility toggle */}
                        {exists && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onToggleVisibility(gid);
                                }}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    padding: '0.25rem',
                                    border: 'none',
                                    background: 'transparent',
                                    cursor: 'pointer',
                                    color: isVisible
                                        ? (isActive ? 'rgba(255,255,255,0.9)' : 'var(--color-text-secondary, #aaa)')
                                        : 'var(--color-text-muted, #555)',
                                    opacity: isVisible ? 1 : 0.5,
                                    transition: 'opacity 0.15s ease',
                                }}
                                title={isVisible ? `Hide Group ${gid}` : `Show Group ${gid}`}
                            >
                                {isVisible
                                    ? <Eye size={12} />
                                    : <EyeOff size={12} />
                                }
                            </button>
                        )}
                    </div>
                );
            })}
        </div>
    );
};