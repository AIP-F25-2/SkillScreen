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
        const colorYellow = [255, 215, 0]; // #FFD700
        const colorOrange = [255, 140, 0]; // #FF8C00
        const colorPurple = [46, 0, 62];   // #2E003E

        const lerpColor = (c1: number[], c2: number[], t: number) => {
            return `rgb(${Math.round(c1[0] + (c2[0] - c1[0]) * t)}, ${Math.round(c1[1] + (c2[1] - c1[1]) * t)}, ${Math.round(c1[2] + (c2[2] - c1[2]) * t)})`;
        };

        const render = (time: number) => {
            ctx.fillStyle = "#000000";
            ctx.fillRect(0, 0, width, height);

            ctx.font = `${cellSize}px monospace`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            const t = time * 0.001;
            const cols = Math.ceil(width / cellSize);
            const rows = Math.ceil(height / cellSize);

            for (let y = 0; y < rows; y++) {
                for (let x = 0; x < cols; x++) {
                    const u = x / cols;
                    const v = y / rows;

                    // Wave function
                    // Create a diagonal wave pattern
                    const wave = Math.sin(u * 5 + v * 5 + t) * 0.5 + 0.5;

                    // Secondary noise/variation
                    const variation = Math.cos(u * 10 - v * 10 + t * 1.5) * 0.5 + 0.5;

                    const value = (wave + variation * 0.2) / 1.2;

                    // Character selection
                    // Use * for brighter/higher values, ~ for lower
                    const charIndex = value > 0.5 ? 0 : 1;
                    const char = chars[charIndex];

                    // Color selection
                    let color;
                    if (value > 0.6) {
                        color = lerpColor(colorOrange, colorYellow, (value - 0.6) / 0.4);
                    } else {
                        color = lerpColor(colorPurple, colorOrange, value / 0.6);
                    }

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
