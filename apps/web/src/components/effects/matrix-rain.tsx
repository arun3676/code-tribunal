"use client";

import { useEffect, useRef } from "react";

export function MatrixRain() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (media.matches) {
      return;
    }
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }
    const characters = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿ0123456789";
    let animationId = 0;
    let intervalId = 0;
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    let columns = Math.floor(canvas.width / 12);
    let drops = Array.from({ length: columns }, () => Math.floor(Math.random() * canvas.height));

    const draw = () => {
      if (document.hidden) {
        return;
      }
      columns = Math.floor(canvas.width / 12);
      if (drops.length !== columns) {
        drops = Array.from({ length: columns }, () => Math.floor(Math.random() * canvas.height));
      }
      context.fillStyle = "rgba(5, 8, 5, 0.08)";
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.font = "12px var(--font-mono), monospace";
      context.fillStyle = "#00FF66";
      context.globalAlpha = 0.024;
      for (let index = 0; index < drops.length; index += 1) {
        const char = characters[Math.floor(Math.random() * characters.length)];
        context.fillText(char, index * 12, drops[index]);
        if (drops[index] > canvas.height && Math.random() > 0.985) {
          drops[index] = 0;
        }
        drops[index] += 12;
      }
      context.globalAlpha = 1;
    };

    intervalId = window.setInterval(draw, 96);
    const onResize = () => resize();
    window.addEventListener("resize", onResize);
    const loop = () => {
      animationId = window.requestAnimationFrame(loop);
    };
    loop();
    return () => {
      window.clearInterval(intervalId);
      window.removeEventListener("resize", onResize);
      window.cancelAnimationFrame(animationId);
    };
  }, []);

  return <canvas ref={canvasRef} className="pointer-events-none fixed inset-0 -z-10 h-full w-full opacity-60" aria-hidden="true" />;
}
