import type { Agent } from '../types/simulation';

/**
 * Linear interpolation between two values
 */
export function lerp(start: number, end: number, t: number): number {
    return start * (1 - t) + end * t;
}

/**
 * Interpolates an agent between two states
 */
export function interpolateAgent(prev: Agent, next: Agent, t: number): Agent {
    return {
        ...next, // Keep discrete properties from latest state (trust, skills)
        x: lerp(prev.x, next.x, t),
        y: lerp(prev.y, next.y, t),
        // We could interpolate trust color too if we wanted super smooth color transitions
        trust: lerp(prev.trust, next.trust, t),
    };
}
