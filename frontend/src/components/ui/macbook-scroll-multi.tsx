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
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
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
    const sectionIndex = Math.min(
      Math.floor(latest * sections.length),
      sections.length - 1
    );
    setCurrentSection(sectionIndex);
  });

  const scaleX = useTransform(
    scrollYProgress,
    [0, 0.3],
    [1.2, isMobile ? 1 : 1.5],
  );
  const scaleY = useTransform(
    scrollYProgress,
    [0, 0.3],
    [0.6, isMobile ? 1 : 1.5],
  );
  const translate = useTransform(scrollYProgress, [0, 1], [0, 1500]);
  const rotate = useTransform(scrollYProgress, [0.1, 0.12, 0.3], [-28, -28, 0]);
  
  // Text transforms for sticky effect
  const textTransform = useTransform(scrollYProgress, [0, 0.3], [0, 100]);
  const textOpacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);

  // Sticky text that changes based on current section
  const stickyTextOpacity = useTransform(scrollYProgress, [0.2, 0.3, 0.7, 0.8], [0, 1, 1, 0]);
  const stickyTextY = useTransform(scrollYProgress, [0.2, 0.8], [50, -50]);

  // Image opacity transitions between sections - create all transforms upfront
  const imageOpacities = sections.map((_, index) => {
    const start = index / sections.length;
    const end = (index + 1) / sections.length;
    const mid = (start + end) / 2;
    
    return useTransform(
      scrollYProgress,
      [
        Math.max(0, start - 0.1),
        start,
        mid,
        end,
        Math.min(1, end + 0.1),
      ],
      [0, 0, 1, 1, 0]
    );
  });

  return (
    <div
      ref={ref}
      className="flex min-h-[200vh] shrink-0 scale-[0.35] transform flex-col items-center justify-start py-0 [perspective:800px] sm:scale-50 md:scale-100 md:py-80"
    >
      {/* Initial Title */}
      <motion.h2
        style={{
          translateY: textTransform,
          opacity: textOpacity,
        }}
        className="mb-20 text-center text-3xl font-bold text-neutral-800 dark:text-white"
      >
        {sections[0]?.title || (
          <span>
            This Macbook is built with Tailwindcss. <br /> No kidding.
          </span>
        )}
      </motion.h2>

      {/* Sticky Text that changes */}
      <motion.div
        style={{
          opacity: stickyTextOpacity,
          translateY: stickyTextY,
        }}
        className="sticky top-20 z-50 mb-20 text-center"
      >
        <motion.div
          key={currentSection}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          className="text-3xl font-bold text-neutral-800 dark:text-white"
        >
          {sections[currentSection]?.title}
        </motion.div>
        {sections[currentSection]?.description && (
          <motion.p
            key={`desc-${currentSection}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="mt-4 text-lg text-neutral-600 dark:text-neutral-300"
          >
            {sections[currentSection]?.description}
          </motion.p>
        )}
      </motion.div>

      {/* Macbook with multiple images */}
      <div className="relative [perspective:800px]">
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
        <motion.div
          style={{
            scaleX: scaleX,
            scaleY: scaleY,
            rotateX: rotate,
            translateY: translate,
            transformStyle: "preserve-3d",
            transformOrigin: "top",
          }}
          className="absolute inset-0 h-96 w-[32rem] rounded-2xl bg-[#010101] p-2"
        >
          <div className="absolute inset-0 rounded-lg bg-[#272729]" />
          {/* Multiple images with opacity transitions */}
          {sections.map((section, index) => (
            <motion.img
              key={index}
              src={section.src}
              alt={`Section ${index + 1}`}
              style={{
                opacity: imageOpacities[index],
              }}
              className="absolute inset-0 h-full w-full rounded-lg object-cover object-left-top"
            />
          ))}
        </motion.div>
      </div>

      {/* Base area (keyboard, trackpad, etc.) */}
      <div className="relative -z-10 h-[22rem] w-[32rem] overflow-hidden rounded-2xl bg-gray-200 dark:bg-[#272729]">
        {/* above keyboard bar */}
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
        {badge && <div className="absolute bottom-4 left-4">{badge}</div>}
      </div>
    </div>
  );
};

