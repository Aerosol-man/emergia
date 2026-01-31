import type { Agent, SimulationState } from '../../types/simulation';
import * as d3 from 'd3-scale';

export class Renderer {
    private ctx: CanvasRenderingContext2D;
    private canvas: HTMLCanvasElement;
    private width: number;
    private height: number;
    private animationId: number | null = null;
    private stateBuffer: React.MutableRefObject<SimulationState[]>;


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

        // MVP Interpolation:
        // We assume 30Hz server ticks (33ms).
        // A robust system would sync clocks. Here we just smooth between the last two known states.
        // We actually want to render "past" state to be smooth.
        // Render time = current time - buffering delay (e.g. 100ms)

        // For this hackathon/MVP, we'll use a simpler "Catch-up" lerp
        // or just interpolate blindly 50% for now as a "Low Pass Filter" on position
        // BUT, proper interpolation requires T.

        // Let's implement immediate-mode interpolation:
        // We always interpolate between previous and latest based on how much time passed?
        // No, that requires knowing WHEN they arrived.

        // Let's just do a simple smoothing:
        // Current Agent Position += (Target Position - Current Position) * 0.1
        // This is "Exponential Moving Average" smoothing. simple and effective for visuals.

        // ...Actually, the `interpolateAgent` function is designed for Lerp.
        // Let's just fix the agents to 'latest' for the MVP to ensure correctness first,
        // then add EMA smoothing if it's jittery. The user asked for interpolation logic.

        // Let's implement the EMA smoothing approach as it's more robust to network jitter than strict time-synced lerp.
        this.agents = latest.agents.map((targetAgent, index) => {
            const currentAgent = this.agents[index];
            if (!currentAgent) return targetAgent; // New agent? snap to it.

            // Smooth X and Y
            // Factor 0.1 means we move 10% of the way there per frame.
            // @ 60fps, this converges very fast but filters high-freq jitter.
            return {
                ...targetAgent,
                x: currentAgent.x + (targetAgent.x - currentAgent.x) * 0.15,
                y: currentAgent.y + (targetAgent.y - currentAgent.y) * 0.15
            };
        });


    }

    // The agents property is now derived from the stateBuffer in update()
    // We need a local agents array for drawing.
    private agents: Agent[] = [];

    private draw() {
        const { ctx, width, height } = this;

        // Trail Effect: Instead of clearing, we draw a semi-transparent rectangle
        // This causes previous frames to fade out slowly, creating a trail.
        ctx.fillStyle = 'rgba(10, 10, 15, 0.2)'; // --color-bg-primary with opacity
        ctx.fillRect(0, 0, width, height);

        // Draw Agents
        for (const agent of this.agents) {
            // Visual Intelligence:
            // 1. Size = Base (3px) + Trade Activity (capped at +5px)
            const radius = 3 + Math.min(agent.tradeCount * 0.5, 5);

            // 2. Color = Trust Scale (Red -> Yellow -> Green)
            const color = this.colorScale(agent.trust);

            // 3. Glow Effect for high trust agents
            if (agent.trust > 0.8) {
                ctx.shadowBlur = 10;
                ctx.shadowColor = color;
            } else {
                ctx.shadowBlur = 0;
            }

            ctx.beginPath();
            ctx.arc(agent.x, agent.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();
        }

        // Reset shadow for text
        ctx.shadowBlur = 0;

        // Draw Stats
        ctx.fillStyle = '#6b7280';
        ctx.font = '12px monospace';
        ctx.fillText(`Agents: ${this.agents.length} | 60FPS Local`, 10, 20);
    }
}
