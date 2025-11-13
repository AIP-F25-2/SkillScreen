"use client";
import React, { useEffect, useRef, useState } from "react";
import { MotionValue, motion, useScroll, useTransform, useMotionValueEvent } from "motion/react";
import { cn } from "@/lib/utils";
import { Keypad, Trackpad, SpeakerGrid } from "./macbook-scroll";

interface ImageSection {
  src: string;
  title: string | React.ReactNode;
  description?: string | React.ReactNode;
}

export const MacbookScrollMulti = ({
  sections,
  showGradient = false,
  badge,
}: {
  sections: ImageSection[];
  showGradient?: boolean;
  badge?: React.ReactNode;
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end end"],
  });

  const [isMobile, setIsMobile] = useState(false);
  const [currentSection, setCurrentSection] = useState(0);

  useEffect(() => {
    if (window && window.innerWidth < 768) {
      setIsMobile(true);
    }
  }, []);

  // Calculate which section to show based on scroll progress
  useMotionValueEvent(scrollYProgress, "change", (latest) => {
    // Each section gets equal portion of scroll
    const sectionIndex = Math.min(
      Math.floor(latest * sections.length),
      sections.length - 1
    );
    setCurrentSection(Math.max(0, sectionIndex));
  });

  // Animation phases
  const tiltEnd = 0.1; // First 10% for tilt animation
  const macbookExitEnd = 0.2; // 10-20% MacBook moves away
  
  // Lid animation (screen)
  const scaleX = useTransform(
    scrollYProgress,
    [0, tiltEnd * 0.7, tiltEnd],
    [1.2, isMobile ? 1 : 1.5, isMobile ? 1 : 1.5]
  );
  const scaleY = useTransform(
    scrollYProgress,
    [0, tiltEnd * 0.7, tiltEnd],
    [0.6, isMobile ? 1 : 1.5, isMobile ? 1 : 1.5]
  );
  const translate = useTransform(scrollYProgress, [0, 1], [0, 0]);
  const rotate = useTransform(
    scrollYProgress, 
    [0, tiltEnd * 0.5, tiltEnd * 0.8, tiltEnd], 
    [-28, -28, 0, 0]
  );
  
  // MacBook hardware (base, lid frame) moves away after tilt
  const macbookOpacity = useTransform(
    scrollYProgress,
    [tiltEnd, tiltEnd + 0.05, macbookExitEnd],
    [1, 0.5, 0]
  );
  
  const macbookScale = useTransform(
    scrollYProgress,
    [tiltEnd, macbookExitEnd],
    [1, 0.3]
  );
  
  const macbookTranslateY = useTransform(
    scrollYProgress,
    [tiltEnd, macbookExitEnd],
    [0, -200]
  );
  
  // Image starts fitting MacBook screen, then expands as MacBook fades
  const imageContainerScale = useTransform(
    scrollYProgress,
    [0, tiltEnd, macbookExitEnd, macbookExitEnd + 0.05],
    [
      1,                        // Fits inside MacBook screen perfectly
      1,                        // Stays same size through tilt
      isMobile ? 2.0 : 2.5,     // Expands as MacBook fades
      isMobile ? 2.2 : 2.8      // Final parallax size (not too zoomed)
    ]
  );


  // Calculate scroll ranges for each section (after MacBook exits)
  const sectionScrollRanges = sections.map((_, index) => {
    const availableScroll = 1 - macbookExitEnd;
    const sectionSize = availableScroll / sections.length;
    const start = macbookExitEnd + (index * sectionSize);
    const end = macbookExitEnd + ((index + 1) * sectionSize);
    return { start, end, mid: (start + end) / 2 };
  });

  // Image opacities that work for both MacBook screen and expanded view
  const imageOpacities = sections.map((_, index) => {
    const { start, end } = sectionScrollRanges[index];
    
    if (index === 0) {
      // First image: visible immediately as MacBook opens, stays through section
      const fadeOut = end - (end - start) * 0.15;
      return useTransform(
        scrollYProgress,
        [0, 0.02, fadeOut, end],
        [1, 1, 1, 0]
      );
    }
    
    // Other images: fade in at their section
    const fadeIn = start + (end - start) * 0.1;
    const fadeOut = end - (end - start) * 0.15;
    
    return useTransform(
      scrollYProgress,
      [start, fadeIn, fadeOut, end],
      [0, 1, 1, 0]
    );
  });

  // Side text opacity for each section (appears beside the images)
  const sideTextOpacities = sections.map((_, index) => {
    const { start, end } = sectionScrollRanges[index];
    
    if (index === 0) {
      // First text appears after MacBook exits
      const fadeIn = macbookExitEnd;
      const fullVisible = macbookExitEnd + 0.05;
      const stayVisible = end - (end - start) * 0.2;
      const fadeOut = end - (end - start) * 0.1;
      
      return useTransform(
        scrollYProgress,
        [fadeIn, fullVisible, stayVisible, fadeOut, end],
        [0, 1, 1, 0.5, 0]
      );
    }
    
    const fadeIn = start + (end - start) * 0.1;
    const fullVisible = start + (end - start) * 0.2;
    const stayVisible = end - (end - start) * 0.2;
    const fadeOut = end - (end - start) * 0.1;
    
    return useTransform(
      scrollYProgress,
      [start, fadeIn, fullVisible, stayVisible, fadeOut, end],
      [0, 0.5, 1, 1, 0.5, 0]
    );
  });

  // Side text translate (slides in from side)
  const sideTextTranslates = sections.map((_, index) => {
    const { start, end } = sectionScrollRanges[index];
    
    if (index === 0) {
      const fadeIn = macbookExitEnd;
      const fullVisible = macbookExitEnd + 0.05;
      return useTransform(
        scrollYProgress,
        [fadeIn, fullVisible],
        [-80, 0]
      );
    }
    
    const fadeIn = start + (end - start) * 0.1;
    const fullVisible = start + (end - start) * 0.2;
    
    return useTransform(
      scrollYProgress,
      [start, fadeIn, fullVisible],
      index % 2 === 0 ? [-80, -40, 0] : [80, 40, 0]
    );
  });

  return (
    <div
      ref={ref}
      className="relative w-full bg-transparent"
      style={{ 
        height: `${150 + sections.length * 100}vh` 
      }}
    >
      {/* Sticky container for MacBook and side text - stays fixed during scroll */}
      <div className="sticky top-0 left-0 w-full h-screen flex items-center justify-center overflow-hidden">
        <div className="relative w-full h-full max-w-[1920px] mx-auto px-4">
          {/* Side text that alternates left/right for each section */}
          {sections.map((section, index) => (
            <motion.div
              key={`text-${index}`}
              style={{
                opacity: sideTextOpacities[index],
                translateX: sideTextTranslates[index],
              }}
              className={cn(
                "absolute top-1/2 -translate-y-1/2 z-40 max-w-xs lg:max-w-md pointer-events-none",
                index % 2 === 0 
                  ? "left-4 md:left-8 lg:left-12 xl:left-16" 
                  : "right-4 md:right-8 lg:right-12 xl:right-16"
              )}
            >
              <div className={cn(
                "p-4 lg:p-6 rounded-2xl backdrop-blur-sm bg-black/20",
                index % 2 === 0 ? "text-left" : "text-right"
              )}>
                <h3 className="text-2xl md:text-3xl lg:text-4xl xl:text-5xl font-bold text-white mb-2 lg:mb-4 drop-shadow-lg leading-tight">
                  {section.title}
                </h3>
                {section.description && (
                  <p className="text-sm md:text-base lg:text-lg xl:text-xl text-white/90 drop-shadow-md leading-snug">
                    {section.description}
                  </p>
                )}
                <div className={cn(
                  "mt-4 lg:mt-6 text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-bold",
                  "bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent drop-shadow-2xl"
                )}>
                  #{String(index + 1).padStart(3, '0')}
                </div>
              </div>
            </motion.div>
          ))}

          {/* MacBook screen container - tilts with images inside, doesn't fade */}
          <motion.div
            className="absolute inset-0 flex items-center justify-center pointer-events-none z-20 scale-[0.35] sm:scale-50 md:scale-75 lg:scale-90"
            style={{
              scaleX: scaleX,
              scaleY: scaleY,
              rotateX: rotate,
              translateY: translate,
              transformStyle: "preserve-3d",
              transformOrigin: "top",
            }}
          >
            {/* MacBook screen frame */}
            <div className="relative h-96 w-[32rem] rounded-2xl bg-[#010101] p-2">
              <div className="absolute inset-0 rounded-lg bg-[#272729] overflow-visible">
                {/* Images INSIDE the screen that expand */}
                <motion.div
                  className="absolute inset-0"
                  style={{
                    scale: imageContainerScale,
                  }}
                >
                  {sections.map((section, index) => (
                    <motion.img
                      key={`screen-image-${index}`}
                      src={section.src}
                      alt={`Section ${index + 1}`}
                      style={{
                        opacity: imageOpacities[index],
                      }}
                      className="absolute inset-0 w-full h-full object-cover rounded-lg shadow-2xl"
                    />
                  ))}
                </motion.div>
              </div>
            </div>
          </motion.div>

          {/* MacBook hardware (frame, keyboard) - fades away */}
          <motion.div 
            className="absolute inset-0 flex items-center justify-center scale-[0.35] sm:scale-50 md:scale-75 lg:scale-90 z-10 pointer-events-none"
            style={{
              opacity: macbookOpacity,
              scale: macbookScale,
              translateY: macbookTranslateY,
            }}
          >
            <div className="relative flex flex-col items-center justify-start">
              <div className="relative [perspective:800px]">
                {/* Lid (closed) */}
                <div
                  style={{
                    transform: "perspective(800px) rotateX(-25deg) translateZ(0px)",
                    transformOrigin: "bottom",
                    transformStyle: "preserve-3d",
                  }}
                  className="relative h-[12rem] w-[32rem] rounded-2xl bg-[#010101] p-2"
                >
                  <div
                    style={{
                      boxShadow: "0px 2px 0px 2px #171717 inset",
                    }}
                    className="absolute inset-0 flex items-center justify-center rounded-lg bg-[#010101]"
                  >
                    {badge}
                  </div>
                </div>
                
                {/* Lid (screen frame/bezel - fades with hardware) */}
                <motion.div
                  style={{
                    scaleX: scaleX,
                    scaleY: scaleY,
                    rotateX: rotate,
                    translateY: translate,
                    transformStyle: "preserve-3d",
                    transformOrigin: "top",
                  }}
                  className="absolute inset-0 h-96 w-[32rem] rounded-2xl bg-[#010101] p-2 pointer-events-none"
                >
                  {/* Screen bezel - this fades with the hardware */}
                  <div className="absolute inset-0 rounded-lg bg-[#272729] pointer-events-none" />
                </motion.div>
              </div>

              {/* Base area (keyboard, trackpad, etc.) */}
              <div className="relative -z-10 h-[22rem] w-[32rem] overflow-hidden rounded-2xl bg-gray-200 dark:bg-[#272729]">
                <div className="relative h-10 w-full">
                  <div className="absolute inset-x-0 mx-auto h-4 w-[80%] bg-[#050505]" />
                </div>
                <div className="relative flex">
                  <div className="mx-auto h-full w-[10%] overflow-hidden">
                    <SpeakerGrid />
                  </div>
                  <div className="mx-auto h-full w-[80%]">
                    <Keypad />
                  </div>
                  <div className="mx-auto h-full w-[10%] overflow-hidden">
                    <SpeakerGrid />
                  </div>
                </div>
                <Trackpad />
                <div className="absolute inset-x-0 bottom-0 mx-auto h-2 w-20 rounded-tl-3xl rounded-tr-3xl bg-gradient-to-t from-[#272729] to-[#050505]" />
                {showGradient && (
                  <div className="absolute inset-x-0 bottom-0 z-50 h-40 w-full bg-gradient-to-t from-white via-white to-transparent dark:from-black dark:via-black"></div>
                )}
              </div>
            </div>
          </motion.div>

        </div>
      </div>
    </div>
  );
};

