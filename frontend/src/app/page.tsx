import NavBar from '@/components/NavBar';
import Hero from '@/components/Hero';
import Features from '@/components/Features';

import { AnimatedGradientBackground } from '@/components/ui/animated-gradient-background';

export default function Home() {
  
  return (
    <div className="min-h-screen relative">
      <AnimatedGradientBackground
        startingGap={110}
        Breathing={true}
        gradientColors={[
          "#1a1a1a",
          "#234C6A",
          "#456882",
          "#1B3C53",
          "#2979FF"
        ]}
        gradientStops={[20, 40, 60, 80, 100]}
        animationSpeed={0.015}
        breathingRange={3}
        topOffset={-20}
        containerClassName="opacity-90"
      />
      {/* Main content */}
      <div className="relative z-10">
        <NavBar />
        <Hero />
        <Features />
      </div>
    </div>
  );
}
