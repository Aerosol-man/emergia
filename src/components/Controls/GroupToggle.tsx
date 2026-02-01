import React from 'react';
import { Eye } from 'lucide-react';

const MAX_GROUPS = 5;

interface GroupToggleProps {
    activeGroupId: number;
    existingGroupIds: number[];
    visibleGroupIds: Set<number>;
    onSwitchGroup: (groupId: number) => void;
    // onToggleVisibility: (groupId: number) => void; // Unused now
    highlightedGroupId: number | null;
    onToggleHighlight: (groupId: number) => void;
}

export const GroupToggle: React.FC<GroupToggleProps> = ({
    activeGroupId,
    existingGroupIds,
    visibleGroupIds, // Kept for now if we want to show visibility state in future, but could remove
    onSwitchGroup,
    // onToggleVisibility,
    highlightedGroupId,
    onToggleHighlight,
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
                // const isVisible = visibleGroupIds.has(gid);

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

                        {/* Highlight toggle (replaces visibility) */}
                        {exists && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onToggleHighlight(gid);
                                }}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    padding: '0.25rem',
                                    border: 'none',
                                    background: 'transparent',
                                    cursor: 'pointer',
                                    color: highlightedGroupId === gid
                                        ? '#a855f7' // Purple when highlighted
                                        : 'var(--color-text-secondary, #aaa)',
                                    opacity: 1, // Always fully opaque to show it's interactable
                                    transition: 'color 0.15s ease',
                                }}
                                title={highlightedGroupId === gid ? `Remove Highlight from Group ${gid}` : `Highlight Group ${gid}`}
                            >
                                {highlightedGroupId === gid
                                    ? <Eye size={12} style={{ fill: 'currentColor' }} /> // Filled eye when highlighted
                                    : <Eye size={12} />
                                }
                            </button>
                        )}
                    </div>
                );
            })}
        </div>
    );
};