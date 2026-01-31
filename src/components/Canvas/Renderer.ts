import type { Agent, SimulationState } from '../../types/simulation';
import * as d3 from 'd3-scale';

export class Renderer {
    private ctx: CanvasRenderingContext2D;
    private canvas: HTMLCanvasElement;
    private width: number;
    private height: number;
    private animationId: number | null = null;
    private stateBuffer: React.MutableRefObject<SimulationState[]>;
    private serverBounds: [number, number] | null = null;

    // Animation State
    private flashEvents = new Map<number, number>(); // agentId -> timestamp
    private readonly FLASH_DURATION = 300; // ms

    // Scales
    private colorScale = d3.scaleLinear<string>()
        .domain([0, 0.5, 1])
        .range(['#ef4444', '#eab308', '#22c55e']) // Red -> Yellow -> Green
        .clamp(true);

    constructor(canvas: HTMLCanvasElement, width: number, height: number, stateBuffer: React.MutableRefObject<SimulationState[]>) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d', { alpha: false }) as CanvasRenderingContext2D; // optimization
        this.width = width;
        this.height = height;
        this.stateBuffer = stateBuffer;

        this.resize(width, height);
    }

    public resize(width: number, height: number) {
        this.width = width;
        this.height = height;

        // Canvas resolution must match CSS size for sharpness
        // In a real app we might handle DPR (devicePixelRatio) here
        this.canvas.width = width;
        this.canvas.height = height;
    }

    public start() {
        if (!this.animationId) {
            this.loop(); // Pass initial timestamp
        }
    }

    public stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    private loop = () => {
        this.update();
        this.draw();
        this.animationId = requestAnimationFrame(this.loop);
    };

    private update() {
        const buffer = this.stateBuffer.current;
        if (buffer.length < 2) {
            if (buffer.length === 1) {
                this.agents = buffer[0].agents;
            }
            return;
        }

        const latest = buffer[buffer.length - 1];
        if (latest.bounds) {
            this.serverBounds = latest.bounds;
        }

        // Detect trade events for animations
        // We compare the previous known state of agents with the new state
        // For efficiency in this loop, we check against `this.agents` (which holds the previous interpolated state)
        // But `this.agents` might be re-ordered or incomplete if agents die/spawn.
        // However, assuming ID stability:
        const currentAgentMap = new Map(this.agents.map(a => [a.id, a]));

        // Update agents with smoothing
        this.agents = latest.agents.map((targetAgent) => {
            const currentAgent = currentAgentMap.get(targetAgent.id);

            if (currentAgent) {
                // Detect trade count increase
                if (targetAgent.tradeCount > currentAgent.tradeCount) {
                    // Trigger flash
                    this.flashEvents.set(targetAgent.id, performance.now());
                }

                // Smooth position
                return {
                    ...targetAgent,
                    x: currentAgent.x + (targetAgent.x - currentAgent.x) * 0.15,
                    y: currentAgent.y + (targetAgent.y - currentAgent.y) * 0.15
                };
            }

            // New agent? snap to it.
            return targetAgent;
        });

        // Prune old flashes occasionally or just let them expire in draw
        // (Clean up happen in draw for visual correctness)
    }

    // The agents property is now derived from the stateBuffer in update()
    // We need a local agents array for drawing.
    private agents: Agent[] = [];

    private draw() {
        const { ctx, width, height } = this;
        const now = performance.now();

        // Trail Effect
        ctx.fillStyle = 'rgba(10, 10, 15, 0.2)';
        ctx.fillRect(0, 0, width, height);

        // Draw Agents
        for (const agent of this.agents) {
            // Calculate screen position
            let cx = agent.x;
            let cy = agent.y;

            if (this.serverBounds) {
                cx = (agent.x / this.serverBounds[0]) * width;
                cy = (agent.y / this.serverBounds[1]) * height;
            }

            // 1. Size
            const radius = 3 + Math.min(agent.tradeCount * 0.5, 5);

            // 2. Color
            const color = this.colorScale(agent.trust);

            // 3. Glow Effect
            if (agent.trust > 0.8) {
                ctx.shadowBlur = 10;
                ctx.shadowColor = color;
            } else {
                ctx.shadowBlur = 0;
            }

            // Draw Agent Body
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();

            // 4. Flash Animation
            if (this.flashEvents.has(agent.id)) {
                const startTime = this.flashEvents.get(agent.id)!;
                const elapsed = now - startTime;

                if (elapsed < this.FLASH_DURATION) {
                    const progress = elapsed / this.FLASH_DURATION; // 0 to 1
                    const flashOpacity = (1.0 - progress) * 0.4; // Reduced brightness (max 0.4)
                    const flashRadius = radius * (1.5 + progress); // Expand slightly

                    ctx.beginPath();
                    ctx.arc(cx, cy, flashRadius, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(255, 255, 255, ${flashOpacity})`;
                    ctx.shadowBlur = 15;
                    ctx.shadowColor = 'white';
                    ctx.fill();
                    ctx.shadowBlur = 0; // Reset
                } else {
                    // Expired
                    this.flashEvents.delete(agent.id);
                }
            }
        }

        // Reset shadow for text
        ctx.shadowBlur = 0;

        // Draw Stats
        ctx.fillStyle = '#6b7280';
        ctx.font = '12px monospace';
        ctx.fillText(`Agents: ${this.agents.length} | 60FPS Local`, 10, 20);
    }
}
