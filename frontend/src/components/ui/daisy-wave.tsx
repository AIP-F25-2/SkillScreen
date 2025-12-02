"use client";

import React, { useEffect, useRef } from "react";

interface DaisyWaveProps {
    className?: string;
    style?: React.CSSProperties;
}

export function DaisyWave({ className, style }: DaisyWaveProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number>();

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let width = canvas.width;
        let height = canvas.height;

        const resize = () => {
            if (canvas.parentElement) {
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight;
                width = canvas.width;
                height = canvas.height;
            }
        };

        window.addEventListener("resize", resize);
        resize();

        const chars = ["*", "~"];
        const cellSize = 24; // Adjust for density

        // Colors
        const colorDeepBlue = [27, 60, 83];   // #1B3C53 (Requested)
        const colorLightBlue = [100, 181, 246]; // Lighter blue for contrast
        const colorDark = [15, 23, 42];       // #0F172A (Background match)

        const lerpColor = (c1: number[], c2: number[], t: number) => {
            return `rgb(${Math.round(c1[0] + (c2[0] - c1[0]) * t)}, ${Math.round(c1[1] + (c2[1] - c1[1]) * t)}, ${Math.round(c1[2] + (c2[2] - c1[2]) * t)})`;
        };

        const render = (time: number) => {
            ctx.fillStyle = "#0F172A"; // Match app background
            ctx.fillRect(0, 0, width, height);

            ctx.font = `${cellSize}px monospace`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            const t = time * 0.001; // Speed 1
            const cols = Math.ceil(width / cellSize);
            const rows = Math.ceil(height / cellSize);

            // Parameters
            const amplitude = 0.42;
            const frequency = 0.51;
            const angle = 90 * (Math.PI / 180); // Vertical (90 degrees)

            const cosAngle = Math.cos(angle);
            const sinAngle = Math.sin(angle);

            for (let y = 0; y < rows; y++) {
                for (let x = 0; x < cols; x++) {
                    // Normalize coordinates -1 to 1
                    const u = (x / cols) * 2 - 1;
                    const v = (y / rows) * 2 - 1;

                    // Rotate coordinates based on angle
                    // We want the wave to propagate in the direction of the angle
                    const rotatedU = u * cosAngle + v * sinAngle;

                    // Sine wave function
                    // Frequency needs to be higher for the grid scale, multiplying by 10 as a baseline
                    const wave = Math.sin(rotatedU * (frequency * 10) + t) * amplitude;

                    // Map -1..1 to 0..1 for value
                    const value = (wave + 1) / 2;

                    // Character selection
                    const charIndex = value > 0.5 ? 0 : 1;
                    const char = chars[charIndex];

                    // Color selection
                    // Gradient from Deep Blue to Light Blue
                    const color = lerpColor(colorDeepBlue, colorLightBlue, value);

                    ctx.fillStyle = color;

                    // Draw character
                    const posX = x * cellSize + cellSize / 2;
                    const posY = y * cellSize + cellSize / 2;

                    ctx.fillText(char, posX, posY);
                }
            }
            animationRef.current = requestAnimationFrame(render);
        };

        animationRef.current = requestAnimationFrame(render);

        return () => {
            window.removeEventListener("resize", resize);
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, []);

    return (
        <div className={className} style={{ width: "100%", height: "100%", ...style }}>
            <canvas ref={canvasRef} style={{ display: "block" }} />
        </div>
    );
}
