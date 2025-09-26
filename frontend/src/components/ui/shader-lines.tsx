"use client"

import { useEffect, useRef } from "react"
import { motion } from 'framer-motion'

declare global {
  interface Window {
    THREE: any
  }
}

interface ShaderAnimationProps {
  currentStep?: number;
  totalSteps?: number;
  progress?: number;
  rippleEffect?: boolean;
  textAnimation?: boolean;
  isCompleteRipple?: boolean;
  fadeOut?: boolean;
}

export function ShaderAnimation({ currentStep = 1, totalSteps = 3, progress = 0, rippleEffect = false, textAnimation = false, isCompleteRipple = false, fadeOut = false }: ShaderAnimationProps) {
  const rippleTimeRef = useRef(0);
  const isRipplingRef = useRef(false);
  const textTimeRef = useRef(0);
  const isTextAnimatingRef = useRef(false);
  const noMoreRingsRef = useRef(false);
  const hasCompletedRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null)
  
  const sceneRef = useRef<{
    camera: any
    scene: any
    renderer: any
    uniforms: any
    animationId: number | null
  }>({
    camera: null,
    scene: null,
    renderer: null,
    uniforms: null,
    animationId: null,
  })

  useEffect(() => {
    let script: HTMLScriptElement | null = null;
    
    // Only load Three.js if it's not already loaded
    if (!window.THREE) {
      script = document.createElement("script");
      script.src = "https://cdnjs.cloudflare.com/ajax/libs/three.js/89/three.min.js";
    script.onload = () => {
      if (containerRef.current && window.THREE) {
          initThreeJS();
      }
      };
      document.head.appendChild(script);
    } else if (containerRef.current) {
      initThreeJS();
    }

    return () => {
      // Cleanup
      if (sceneRef.current.animationId) {
        cancelAnimationFrame(sceneRef.current.animationId);
      }
      if (sceneRef.current.renderer) {
        sceneRef.current.renderer.dispose();
      }
      if (script) {
        document.head.removeChild(script);
      }
    };
  }, []) // Only initialize once

  // Update uniforms when props change without re-initializing
  useEffect(() => {
    if (sceneRef.current.uniforms) {
      sceneRef.current.uniforms.progress.value = progress;
      sceneRef.current.uniforms.currentStep.value = currentStep;
      sceneRef.current.uniforms.totalSteps.value = totalSteps;
    }
  }, [currentStep, progress, totalSteps])

  // Handle ripple effect trigger
  useEffect(() => {
    if (rippleEffect && sceneRef.current.uniforms && !isRipplingRef.current) {
      isRipplingRef.current = true;
      rippleTimeRef.current = 0;
      sceneRef.current.uniforms.isRippling.value = 1.0;
      sceneRef.current.uniforms.rippleTime.value = 0;
    }
  }, [rippleEffect])

  // Handle text animation trigger
  useEffect(() => {
    if (textAnimation && sceneRef.current.uniforms && !isTextAnimatingRef.current) {
      isTextAnimatingRef.current = true;
      textTimeRef.current = 0;
      sceneRef.current.uniforms.isTextAnimating.value = 1.0;
      sceneRef.current.uniforms.textTime.value = 0;
    }
  }, [textAnimation])

  const initThreeJS = () => {
    if (!containerRef.current || !window.THREE) return

    const THREE = window.THREE
    const container = containerRef.current

    // Clear any existing content
    container.innerHTML = ""

    // Initialize camera
    const camera = new THREE.Camera()
    camera.position.z = 1

    // Initialize scene
    const scene = new THREE.Scene()

    // Create geometry
    const geometry = new THREE.PlaneBufferGeometry(2, 2)

    // Define uniforms
    const uniforms = {
      time: { type: "f", value: 1.0 },
      resolution: { type: "v2", value: new THREE.Vector2() },
      progress: { type: "f", value: progress },
      currentStep: { type: "f", value: currentStep },
      totalSteps: { type: "f", value: totalSteps },
      rippleTime: { type: "f", value: 0.0 },
      isRippling: { type: "f", value: 0.0 },
      textTime: { type: "f", value: 0.0 },
      isTextAnimating: { type: "f", value: 0.0 },
      freezeTime: { type: "f", value: 0.0 },
    }

    // Vertex shader
    const vertexShader = `
      void main() {
        gl_Position = vec4( position, 1.0 );
      }
    `

    // Fragment shader
    const fragmentShader = `
      #define TWO_PI 6.2831853072
      #define PI 3.14159265359

      precision highp float;
      uniform vec2 resolution;
      uniform float time;
      uniform float progress;
      uniform float currentStep;
      uniform float totalSteps;
      uniform float rippleTime;
      uniform float isRippling;
      uniform float freezeTime;
      uniform float textTime;
      uniform float isTextAnimating;
        
      float random (in float x) {
          return fract(sin(x)*1e4);
      }
      float random (vec2 st) {
          return fract(sin(dot(st.xy,
                               vec2(12.9898,78.233)))*
              43758.5453123);
      }
      
      // Simple bitmap font for letters
      float letter(vec2 coord, float letter_code) {
          coord = floor(coord * 8.0) / 8.0;
          float x = coord.x;
          float y = coord.y;
          
          // Letter patterns (simplified 8x8 bitmap)
          if (letter_code < 0.5) { // W
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  if ((x < 0.2 || x > 0.8) && y < 0.8) return 1.0;
                  if (y < 0.2 && x > 0.3 && x < 0.7) return 1.0;
                  if (abs(x - 0.5) < 0.1 && y > 0.2 && y < 0.6) return 1.0;
              }
          } else if (letter_code < 1.5) { // E
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  if (x < 0.2) return 1.0;
                  if (y > 0.8 || y < 0.2 || (y > 0.4 && y < 0.6)) return 1.0;
              }
          } else if (letter_code < 2.5) { // L
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  if (x < 0.2 || y < 0.2) return 1.0;
              }
          } else if (letter_code < 3.5) { // C
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  float dist = distance(coord, vec2(0.5, 0.5));
                  if (dist > 0.3 && dist < 0.5 && x < 0.7) return 1.0;
              }
          } else if (letter_code < 4.5) { // O
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  float dist = distance(coord, vec2(0.5, 0.5));
                  if (dist > 0.2 && dist < 0.4) return 1.0;
              }
          } else if (letter_code < 5.5) { // M
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  if (x < 0.2 || x > 0.8) return 1.0;
                  if (y > 0.6 && abs(x - 0.5) < 0.1) return 1.0;
              }
          } else if (letter_code < 6.5) { // T
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  if (y > 0.8 || (abs(x - 0.5) < 0.1 && y < 0.8)) return 1.0;
              }
          } else if (letter_code < 7.5) { // I
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  if (abs(x - 0.5) < 0.1 || y > 0.8 || y < 0.2) return 1.0;
              }
          } else if (letter_code < 8.5) { // N
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  if (x < 0.2 || x > 0.8 || abs(x - y) < 0.1) return 1.0;
              }
          } else if (letter_code < 9.5) { // V
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  if (y > 0.5 && (x < 0.2 || x > 0.8)) return 1.0;
                  if (y < 0.5 && abs(x - 0.5) < (0.5 - y)) return 1.0;
              }
          } else if (letter_code < 10.5) { // R
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  if (x < 0.2) return 1.0;
                  if (y > 0.8 || (y > 0.4 && y < 0.6)) return 1.0;
                  if (y > 0.6 && x > 0.2 && x < 0.8) return 1.0;
                  if (y < 0.4 && x > y + 0.3) return 1.0;
              }
          } else if (letter_code < 11.5) { // U
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  if ((x < 0.2 || x > 0.8) && y > 0.2) return 1.0;
                  if (y < 0.2 && x > 0.2 && x < 0.8) return 1.0;
              }
          } else if (letter_code < 12.5) { // A
              if (x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0) {
                  if ((x < 0.2 || x > 0.8) && y > 0.2) return 1.0;
                  if (y > 0.8 && x > 0.2 && x < 0.8) return 1.0;
                  if (y > 0.4 && y < 0.6 && x > 0.2 && x < 0.8) return 1.0;
              }
          }
          return 0.0;
      }
      
      varying vec2 vUv;

      void main(void) {
        vec2 uv = (gl_FragCoord.xy * 2.0 - resolution.xy) / min(resolution.x, resolution.y);
        
        // Adjust mosaic scale based on progress
        float progressFactor = 1.0 + progress * 2.0;
        vec2 fMosaicScal = vec2(4.0, 2.0) * progressFactor;
        vec2 vScreenSize = vec2(256,256);
        uv.x = floor(uv.x * vScreenSize.x / fMosaicScal.x) / (vScreenSize.x / fMosaicScal.x);
        uv.y = floor(uv.y * vScreenSize.y / fMosaicScal.y) / (vScreenSize.y / fMosaicScal.y);       
          
        // Use frozen time if set, otherwise use normal time
        float effectiveTime = freezeTime > 0.0 ? freezeTime : time;
        
        // Adjust animation speed and pattern based on current step
        float stepFactor = currentStep / totalSteps;
        float t = effectiveTime * (0.06 + stepFactor * 0.04) + random(uv.x) * (0.4 + progress * 0.3);
        float lineWidth = 0.0008 + progress * 0.0004;

        vec3 color = vec3(0.0);
        
        if (freezeTime > 0.0) {
          // After complete: create completely static pattern without time-based variations
          // Use only spatial coordinates for a static fractal pattern
          for(int j = 0; j < 3; j++){
            for(int i=0; i < 5; i++){
              // Create static rings based only on distance, no time component
              float staticRings = abs(sin(length(uv) * 20.0 + float(i) * 0.5) * cos(length(uv) * 15.0 + float(j) * 0.3));
              float intensity = lineWidth * float(i*i) / (staticRings + 0.1);
              color[j] += intensity * (1.0 + progress * 0.5) * 0.2; // Very dim static pattern
            }
          }
        } else {
          // Normal state: animated flowing pattern
          for(int j = 0; j < 3; j++){
            for(int i=0; i < 5; i++){
              float intensity = lineWidth * float(i*i) / abs(fract(t - 0.01*float(j)+float(i)*0.01)*1.0 - length(uv));
              color[j] += intensity * (1.0 + progress * 0.5);        
            }
          }
        }

        // Define color palette using conditional logic: #1a1a1a, #234C6A, #456882, #1B3C53, #2979FF
        float colorIndex = fract(progress * 2.0 + effectiveTime * 0.1) * 5.0;
        vec3 paletteColor;
        
        if (colorIndex < 1.0) {
          paletteColor = mix(vec3(0.102, 0.102, 0.102), vec3(0.137, 0.298, 0.416), fract(colorIndex));
        } else if (colorIndex < 2.0) {
          paletteColor = mix(vec3(0.137, 0.298, 0.416), vec3(0.275, 0.408, 0.510), fract(colorIndex));
        } else if (colorIndex < 3.0) {
          paletteColor = mix(vec3(0.275, 0.408, 0.510), vec3(0.106, 0.235, 0.325), fract(colorIndex));
        } else if (colorIndex < 4.0) {
          paletteColor = mix(vec3(0.106, 0.235, 0.325), vec3(0.161, 0.475, 1.0), fract(colorIndex));
        } else {
          paletteColor = mix(vec3(0.161, 0.475, 1.0), vec3(0.102, 0.102, 0.102), fract(colorIndex));
        }
        
        // Apply the palette color to the pattern
        vec3 baseColor = mix(
          paletteColor * color[0] * 1.5,
          paletteColor * color[1] * 1.2, 
          progress * 0.3
        ) + paletteColor * color[2] * 0.8;
        
        // Add ripple effect
        if (isRippling > 0.5) {
          float dist = length(uv);
          float rippleRadius = rippleTime * 2.5; // Expanding radius
          
          // Create the same line pattern but faster and green
          float rippleT = time * 0.15 + random(uv.x) * 0.4; // Faster than base
          float rippleLineWidth = 0.001;

          vec3 rippleColor = vec3(0.0);
          for(int j = 0; j < 3; j++){
            for(int i=0; i < 5; i++){
              float intensity = rippleLineWidth * float(i*i) / 
                abs(fract(rippleT - 0.01*float(j)+float(i)*0.01)*1.0 - length(uv));
              rippleColor[j] += intensity * 2.0; // Brighter
            }
          }
          
          // Keep same silver/white color as base animation but brighter
          vec3 silverRipple = vec3(rippleColor[2], rippleColor[1], rippleColor[0]) * 2.0;
          
          // Only show the ripple in an expanding ring
          float rippleWidth = 0.4;
          float rippleMask = smoothstep(rippleRadius - rippleWidth, rippleRadius, dist) * 
                            smoothstep(rippleRadius + rippleWidth, rippleRadius, dist);
          
          // Strong fade effect
          float fadeOut = (1.0 - rippleTime) * rippleMask * 2.0;
          
          // Override base color more aggressively
          baseColor = mix(baseColor, silverRipple, min(fadeOut, 1.0));
        }
        
        // No shader text rendering - using HTML text overlay instead
        
        gl_FragColor = vec4(baseColor, 1.0);
      }
    `

    // Create material
    const material = new THREE.ShaderMaterial({
      uniforms: uniforms,
      vertexShader: vertexShader,
      fragmentShader: fragmentShader,
    })

    // Create mesh and add to scene
    const mesh = new THREE.Mesh(geometry, material)
    scene.add(mesh)

    // Initialize renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true })
    renderer.setPixelRatio(window.devicePixelRatio)
    container.appendChild(renderer.domElement)

    // Store references
    sceneRef.current = {
      camera,
      scene,
      renderer,
      uniforms,
      animationId: null,
    }

    // Handle resize
    const onWindowResize = () => {
      const rect = container.getBoundingClientRect()
      renderer.setSize(rect.width, rect.height)
      uniforms.resolution.value.x = renderer.domElement.width
      uniforms.resolution.value.y = renderer.domElement.height
    }

    onWindowResize()
    window.addEventListener("resize", onWindowResize, false)

    // Animation loop
    const animate = () => {
      sceneRef.current.animationId = requestAnimationFrame(animate)
      
      // Handle fractal animation timing
      let animationSpeed = 0.015;
      
      // Handle ongoing ripple animation
      if (isRipplingRef.current) {
        rippleTimeRef.current += 0.04; // Faster ripple speed
        uniforms.rippleTime.value = rippleTimeRef.current;
        animationSpeed = 0.05; // Speed up fractal during ring effect
        
        // Reset ripple after animation completes
        if (rippleTimeRef.current >= 1.0) {
          isRipplingRef.current = false;
          uniforms.isRippling.value = 0.0;
          rippleTimeRef.current = 0;
          
          // Only freeze if this is the complete ripple
          if (isCompleteRipple) {
            hasCompletedRef.current = true; // Mark as permanently completed
            noMoreRingsRef.current = true; // Prevent new rings
            uniforms.freezeTime.value = uniforms.time.value; // Freeze at current time
          }
        }
      }

      // Handle ongoing text animation (not used anymore, keeping for compatibility)
      if (isTextAnimatingRef.current) {
        textTimeRef.current += 0.015;
        uniforms.textTime.value = textTimeRef.current;
      }
      
      // Only animate fractal if we haven't completed the final step
      if (!hasCompletedRef.current) {
        uniforms.time.value += animationSpeed;
      }
      
      uniforms.progress.value = progress
      uniforms.currentStep.value = currentStep
      uniforms.totalSteps.value = totalSteps
      
      renderer.render(scene, camera)
    }

    animate()
  }

  return (
    <motion.div
      ref={containerRef}
      className="fixed inset-0 w-full h-full z-0"
      initial={{ opacity: 1 }}
      animate={{ opacity: fadeOut ? 0 : 1 }}
      transition={{ duration: 0.5, ease: "easeInOut" }}
    />
  )
}
