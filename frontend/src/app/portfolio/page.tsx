'use client';

import NavBar from '@/components/NavBar';
import ShaderHero from '@/components/ShaderHero';
import { FeaturesGrid } from '@/components/FeaturesGrid';
import { TeamSection } from '@/components/TeamSection';
import Footer from '@/components/Footer';
import { DitheringShader } from "@/components/ui/dithering-shader";


export default function PortfolioPage() {
    return (
        <div className="relative min-h-screen">
            <div className="fixed inset-0 -z-10">
                <DitheringShader
                    shape="wave"
                    type="8x8"
                    colorBack="#0F172A"
                    colorFront="#1B3C53" // Requested blue color
                    pxSize={4}
                    speed={0.4}
                    className="w-full h-full"
                    width={1920}
                    height={1080}
                />
            </div>

            <div className="relative">
                <div className="absolute top-0 left-0 right-0 z-50">
                    <NavBar />
                </div>
                <ShaderHero />
                <FeaturesGrid />
                <TeamSection />
                <Footer />
            </div>
        </div>
    );
}
