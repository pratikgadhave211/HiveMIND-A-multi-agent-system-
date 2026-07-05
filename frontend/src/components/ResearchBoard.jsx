import React, { useEffect, useRef } from 'react';
import { Shield, Brain, Terminal, Activity, FileText, LayoutDashboard, Settings } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ResearchBoard({ activeTaskName, progressPercent, agents, swarmTemp, throughput }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    function syncSize() {
      const w = canvas.clientWidth || 256;
      const h = canvas.clientHeight || 256;
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
    }
    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(syncSize);
      observer.observe(canvas);
      return () => observer.disconnect();
    }
    syncSize();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) return;

    const vs = `attribute vec2 a_position;
varying vec2 v_texCoord;
void main() {
  v_texCoord = a_position * 0.5 + 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}`;
    const fs = `precision highp float;
uniform float u_time;
uniform vec2 u_resolution;
varying vec2 v_texCoord;

void main() {
    vec2 uv = (v_texCoord - 0.5) * 2.0;
    uv.x *= u_resolution.x / u_resolution.y;

    float dist = length(uv);
    float angle = atan(uv.y, uv.x);

    // AI Purple color: #6366F1
    vec3 color1 = vec3(0.388, 0.4, 0.945);
    // Success Green: #10B981
    vec3 color2 = vec3(0.063, 0.725, 0.506);

    // Futuristic Ring logic
    float ring_inner = 0.6;
    float ring_outer = 0.65;
    
    // Rotating gaps
    float rot = u_time * 2.0;
    float sectors = 8.0;
    float gap = sin(angle * sectors + rot) * 0.5 + 0.5;
    
    float ring = smoothstep(ring_inner, ring_inner + 0.01, dist) - smoothstep(ring_outer - 0.01, ring_outer, dist);
    ring *= gap;

    // Pulse
    float pulse = sin(u_time * 3.0) * 0.05 + 0.95;
    ring *= pulse;

    // Glowing core
    float core = smoothstep(0.5, 0.0, dist) * 0.3 * (sin(u_time * 1.5) * 0.5 + 0.5);
    
    vec3 finalColor = color1 * ring + color1 * core;
    
    // Add some "Success Green" particles or accent
    float accent = smoothstep(0.02, 0.0, length(uv - vec2(cos(u_time), sin(u_time)) * 0.625));
    finalColor += color2 * accent * 1.5;

    gl_FragColor = vec4(finalColor, ring + core + accent);
}`;
    function cs(type, src) {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    }
    const prog = gl.createProgram();
    gl.attachShader(prog, cs(gl.VERTEX_SHADER, vs));
    gl.attachShader(prog, cs(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);

    const pos = gl.getAttribLocation(prog, 'a_position');
    gl.enableVertexAttribArray(pos);
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

    const uTime = gl.getUniformLocation(prog, 'u_time');
    const uRes = gl.getUniformLocation(prog, 'u_resolution');

    let animationId;
    function render(t) {
      gl.viewport(0, 0, canvas.width, canvas.height);
      if (uTime) gl.uniform1f(uTime, t * 0.001);
      if (uRes) gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      animationId = requestAnimationFrame(render);
    }
    render(0);

    return () => cancelAnimationFrame(animationId);
  }, []);

  return (
    <div className="w-full flex flex-col items-center py-8">
      {/* Hero Shader Element */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-64 h-64 rounded-full overflow-hidden border border-[var(--color-ai-accent)]/20 shadow-[0_0_40px_rgba(99,102,241,0.2)]"
      >
        <div className="absolute inset-0 w-full h-full block">
          <canvas ref={canvasRef} className="block w-full h-full"></canvas>
        </div>
        {/* Overlay glass effect */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/40 to-transparent"></div>
      </motion.div>

      <div className="mt-8 text-center">
        <p className="font-mono text-xs text-white uppercase tracking-widest mb-2">Active Swarm Task</p>
        <div className="flex items-baseline justify-center gap-2">
          <span className="text-xl font-bold text-white">{activeTaskName || 'Neural Synthesis'}</span>
          <span className="font-mono text-[var(--color-ai-accent)] bg-[var(--color-ai-accent)]/10 px-2 py-0.5 rounded-full text-sm font-semibold">
            {progressPercent}%
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full max-w-xs mt-6 h-1 bg-neutral-900 rounded-full overflow-hidden">
        <div 
          className="h-full bg-[var(--color-ai-accent)] shadow-[0_0_10px_rgba(99,102,241,0.5)] transition-all duration-500" 
          style={{ width: `${progressPercent}%` }}
        ></div>
      </div>

      {/* Agent Swarm Section */}
      <div className="mt-10 w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white">Agent Swarm</h2>
          <span className="font-mono text-xs text-[var(--color-success)]">{agents.filter(a => a.status === 'running').length} LIVE NODES</span>
        </div>
        <div className="space-y-3 flex flex-col gap-2">
          {agents.map((agent, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 * i }}
              className={`bg-black p-4 rounded-xl flex items-center justify-between border shadow-sm ${agent.status === 'error' ? 'border-red-200' : 'border-neutral-800'}`}
            >
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${
                  agent.status === 'done' ? 'bg-[var(--color-success)]/10 border-[var(--color-success)]/20 text-[var(--color-success)]' :
                  agent.status === 'error' ? 'bg-red-100 border-red-200 text-red-600' :
                  'bg-[var(--color-ai-accent)]/10 border-[var(--color-ai-accent)]/20 text-[var(--color-ai-accent)]'
                }`}>
                  <Brain className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">{agent.name}</p>
                  <p className="font-mono text-[10px] text-white uppercase">{agent.taskDesc || 'Processing'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-bold ${
                  agent.status === 'done' ? 'text-[var(--color-success)]' :
                  agent.status === 'error' ? 'text-red-500' :
                  'text-[var(--color-ai-accent)]'
                }`}>
                  {agent.status.toUpperCase()}
                </span>
                <div className={`w-2 h-2 rounded-full ${
                  agent.status === 'done' ? 'bg-[var(--color-success)]' :
                  agent.status === 'error' ? 'bg-red-500' :
                  'bg-[var(--color-ai-accent)] animate-pulse'
                }`}></div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* System Stats Grid */}
      <div className="mt-8 grid grid-cols-2 gap-4 w-full max-w-md">
        <div className="bg-black p-4 rounded-xl border border-neutral-800 shadow-sm text-center">
          <p className="font-mono text-[10px] text-white uppercase mb-1">Swarm Temp</p>
          <p className="text-lg font-bold text-white">{swarmTemp}°C</p>
        </div>
        <div className="bg-black p-4 rounded-xl border border-neutral-800 shadow-sm text-center">
          <p className="font-mono text-[10px] text-white uppercase mb-1">Throughput</p>
          <p className="text-lg font-bold text-[var(--color-ai-accent)]">{throughput}k/s</p>
        </div>
      </div>
    </div>
  );
}
