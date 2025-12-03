"use client";

import React, { useEffect, useRef } from "react";

// GLSL utility functions
const declarePI = `
#define TWO_PI 6.28318530718
#define PI 3.14159265358979323846
`;

const proceduralHash11 = `
  float hash11(float p) {
    p = fract(p * 0.3183099) + 0.1;
    p *= p + 19.19;
    return fract(p * p);
  }
`;

const proceduralHash21 = `
  float hash21(vec2 p) {
    p = fract(p * vec2(0.3183099, 0.3678794)) + 0.1;
    p += dot(p, p + 19.19);
    return fract(p.x * p.y);
  }
`;

const simplexNoise = `
vec3 permute(vec3 x) { return mod(((x * 34.0) + 1.0) * x, 289.0); }
float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
    -0.577350269189626, 0.024390243902439);
  vec2 i = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1;
  i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
    + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy),
      dot(x12.zw, x12.zw)), 0.0);
  m = m * m;
  m = m * m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
  vec3 g;
  g.x = a0.x * x0.x + h.x * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}
`;

// Vertex shader
const vertexShaderSource = `#version 300 es
precision mediump float;

layout(location = 0) in vec4 a_position;
out vec2 v_uv;

void main() {
  gl_Position = a_position;
  v_uv = a_position.xy * 0.5 + 0.5;
}
`;

// Fragment shader
const fragmentShaderSource = `#version 300 es
precision mediump float;

uniform float u_time;
uniform vec2 u_resolution;
uniform vec4 u_colorBack;
uniform vec4 u_colorFront;
uniform float u_pxSize;
uniform sampler2D u_logoTexture;
uniform float u_logoAspect;
uniform float u_logoScale;

in vec2 v_uv;
out vec4 fragColor;

${simplexNoise}
${declarePI}
${proceduralHash11}
${proceduralHash21}

float getSimplexNoise(vec2 uv, float t) {
  float noise = .5 * snoise(uv - vec2(0., .3 * t));
  noise += .5 * snoise(2. * uv + vec2(0., .32 * t));
  return noise;
}

const int bayer8x8[64] = int[64](
   0, 32,  8, 40,  2, 34, 10, 42,
  48, 16, 56, 24, 50, 18, 58, 26,
  12, 44,  4, 36, 14, 46,  6, 38,
  60, 28, 52, 20, 62, 30, 54, 22,
   3, 35, 11, 43,  1, 33,  9, 41,
  51, 19, 59, 27, 49, 17, 57, 25,
  15, 47,  7, 39, 13, 45,  5, 37,
  63, 31, 55, 23, 61, 29, 53, 21
);

float getBayerValue(vec2 uv, int size) {
  ivec2 pos = ivec2(mod(uv, float(size)));
  int index = pos.y * size + pos.x;
  return float(bayer8x8[index]) / 64.0;
}

void main() {
  float t = .5 * u_time;
  
  // Calculate centered UVs for logo
  // Normalize by the smaller dimension to ensure the logo fits within the screen
  float minDim = min(u_resolution.x, u_resolution.y);
  vec2 screenUV = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / minDim;
  
  vec2 texUV = screenUV / u_logoScale;
  texUV.x /= u_logoAspect;
  texUV += 0.5;
  
  vec4 logoColor = vec4(0.0);
  if (texUV.x >= 0.0 && texUV.x <= 1.0 && texUV.y >= 0.0 && texUV.y <= 1.0) {
      logoColor = texture(u_logoTexture, vec2(texUV.x, 1.0 - texUV.y));
  }
  
  // If inside logo (alpha > threshold), discard or draw background
  if (logoColor.a > 0.1) {
      fragColor = u_colorBack;
      return;
  }

  vec2 uv = gl_FragCoord.xy / u_resolution.xy;
  uv -= .5;
  
  // Apply pixelization
  float pxSize = u_pxSize;
  vec2 pxSizeUv = gl_FragCoord.xy;
  pxSizeUv -= .5 * u_resolution;
  pxSizeUv /= pxSize;
  vec2 pixelizedUv = floor(pxSizeUv) * pxSize / u_resolution.xy;
  pixelizedUv += .5;
  pixelizedUv -= .5;
  
  vec2 shape_uv = pixelizedUv;
  vec2 dithering_uv = pxSizeUv;

  // Wave Shape (Shape 4 from DitheringShader)
  shape_uv *= 4.;
  float wave = cos(.5 * shape_uv.x - 2. * t) * sin(1.5 * shape_uv.x + t) * (.75 + .25 * cos(3. * t));
  float shape = 1. - smoothstep(-1., 1., shape_uv.y + wave);

  // Dithering (8x8)
  float dithering = getBayerValue(dithering_uv, 8);
  dithering -= .5;
  
  float res = step(.5, shape + dithering);

  vec3 fgColor = u_colorFront.rgb * u_colorFront.a;
  float fgOpacity = u_colorFront.a;
  vec3 bgColor = u_colorBack.rgb * u_colorBack.a;
  float bgOpacity = u_colorBack.a;

  vec3 color = fgColor * res;
  float opacity = fgOpacity * res;

  color += bgColor * (1. - opacity);
  opacity += bgOpacity * (1. - opacity);

  fragColor = vec4(color, opacity);
}
`;

interface LogoDitherProps {
  className?: string;
  style?: React.CSSProperties;
  scale?: number;
}

function createShader(gl: WebGL2RenderingContext, type: number, source: string): WebGLShader | null {
  const shader = gl.createShader(type)
  if (!shader) return null

  gl.shaderSource(shader, source)
  gl.compileShader(shader)

  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.error("An error occurred compiling the shaders: " + gl.getShaderInfoLog(shader))
    gl.deleteShader(shader)
    return null
  }

  return shader
}

function createProgram(
  gl: WebGL2RenderingContext,
  vertexShaderSource: string,
  fragmentShaderSource: string,
): WebGLProgram | null {
  const vertexShader = createShader(gl, gl.VERTEX_SHADER, vertexShaderSource)
  const fragmentShader = createShader(gl, gl.FRAGMENT_SHADER, fragmentShaderSource)

  if (!vertexShader || !fragmentShader) return null

  const program = gl.createProgram()
  if (!program) return null

  gl.attachShader(program, vertexShader)
  gl.attachShader(program, fragmentShader)
  gl.linkProgram(program)

  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error("Unable to initialize the shader program: " + gl.getProgramInfoLog(program))
    gl.deleteProgram(program)
    return null
  }

  return program
}

function hexToRgba(hex: string): [number, number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  if (!result) return [0, 0, 0, 1]

  return [
    Number.parseInt(result[1], 16) / 255,
    Number.parseInt(result[2], 16) / 255,
    Number.parseInt(result[3], 16) / 255,
    1,
  ]
}

export function LogoDither({ className, style, scale = 0.35 }: LogoDitherProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const glRef = useRef<WebGL2RenderingContext | null>(null);
  const programRef = useRef<WebGLProgram | null>(null);
  const startTimeRef = useRef<number>(Date.now());
  const logoAspectRef = useRef<number>(1.0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext("webgl2");
    if (!gl) return;
    glRef.current = gl;

    const program = createProgram(gl, vertexShaderSource, fragmentShaderSource);
    if (!program) return;
    programRef.current = program;

    // Attributes
    const positionAttributeLocation = gl.getAttribLocation(program, "a_position");
    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    const positions = [-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1];
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(positionAttributeLocation);
    gl.vertexAttribPointer(positionAttributeLocation, 2, gl.FLOAT, false, 0, 0);

    // Uniforms
    const u_time = gl.getUniformLocation(program, "u_time");
    const u_resolution = gl.getUniformLocation(program, "u_resolution");
    const u_colorBack = gl.getUniformLocation(program, "u_colorBack");
    const u_colorFront = gl.getUniformLocation(program, "u_colorFront");
    const u_pxSize = gl.getUniformLocation(program, "u_pxSize");
    const u_logoTexture = gl.getUniformLocation(program, "u_logoTexture");
    const u_logoAspect = gl.getUniformLocation(program, "u_logoAspect");
    const u_logoScale = gl.getUniformLocation(program, "u_logoScale");

    // Load Logo Texture
    const texture = gl.createTexture();
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, texture);

    // Fill with 1x1 transparent pixel while loading
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 0]));

    const image = new Image();
    image.src = "/logo_out.webp";
    image.onload = () => {
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
      gl.generateMipmap(gl.TEXTURE_2D);
      // Clamp to edge to handle non-power-of-2 images
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);

      logoAspectRef.current = image.width / image.height;
    };

    const resize = () => {
      if (canvas.parentElement) {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
        gl.viewport(0, 0, canvas.width, canvas.height);
      }
    };
    window.addEventListener("resize", resize);
    resize();

    const render = () => {
      const currentTime = (Date.now() - startTimeRef.current) * 0.001;

      gl.useProgram(program);

      if (u_time) gl.uniform1f(u_time, currentTime);
      if (u_resolution) gl.uniform2f(u_resolution, canvas.width, canvas.height);
      if (u_colorBack) gl.uniform4fv(u_colorBack, hexToRgba("#0F172A"));
      if (u_colorFront) gl.uniform4fv(u_colorFront, hexToRgba("#64B5F6"));
      if (u_pxSize) gl.uniform1f(u_pxSize, 4.0);
      if (u_logoTexture) gl.uniform1i(u_logoTexture, 0);
      if (u_logoAspect) gl.uniform1f(u_logoAspect, logoAspectRef.current);
      if (u_logoScale) gl.uniform1f(u_logoScale, scale);

      gl.drawArrays(gl.TRIANGLES, 0, 6);
      animationRef.current = requestAnimationFrame(render);
    };

    animationRef.current = requestAnimationFrame(render);

    return () => {
      window.removeEventListener("resize", resize);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (glRef.current && programRef.current) glRef.current.deleteProgram(programRef.current);
    };
  }, [scale]);

  return (
    <div className={className} style={{ width: "100%", height: "100%", ...style }}>
      <canvas ref={canvasRef} style={{ display: "block" }} />
    </div>
  );
}
