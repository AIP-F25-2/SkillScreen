'use client';

import NavBar from "@/components/NavBar";
import ShaderHero from "@/components/ShaderHero";
import ProjectInfo from "@/components/ProjectInfo";
import DemoSection from "@/components/DemoSection";
import { TeamSection } from "@/components/TeamSection";
import Footer from "@/components/Footer";
import { DitheringShader } from "@/components/ui/dithering-shader";
import { LogoDither } from "@/components/ui/logo-dither";
export default function PortfolioPage() {
    return (
        <div className="relative min-h-screen bg-black">
            {/* Fixed Background Shader */}
            <div className="fixed inset-0 z-0">
                {/* <DitheringShader
                    width={1920}
                    height={1080}
                    colorBack="#0F172A" // Dark Slate
                    colorFront="#1B3C53" // Deep Blue
                    shape="wave"
                    type="8x8"
                    pxSize={6}
                    speed={2}
                    className="w-full h-full opacity-60"
                />*/}
                <LogoDither className="w-full h-full" />
                <div className="absolute inset-0 bg-black/45 pointer-events-none" />
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/20 to-black pointer-events-none" />
            </div>

            <div className="relative z-10">
                <NavBar isPortfolio={true} />
                <ShaderHero />
                <ProjectInfo />
                <DemoSection />
                <TeamSection />
                <Footer isPortfolio={true} />
            </div>
        </div>
    );
}
