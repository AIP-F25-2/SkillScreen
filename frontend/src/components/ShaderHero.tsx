import { Button } from "@/components/ui/button";

export default function ShaderHero() {
    return (
        <div className="relative flex min-h-screen w-full flex-col items-center justify-center overflow-hidden">
            {/* Content Overlay */}
            <div className="relative z-20 flex flex-col items-center text-center px-4 max-w-5xl mx-auto pt-32 pb-16">
                <h1 className="text-6xl md:text-8xl font-bold text-white tracking-tight mb-6 drop-shadow-lg">
                    SkillScreen
                </h1>
                <p className="text-indigo-100 text-xl md:text-3xl max-w-3xl mx-auto mb-10 font-light leading-relaxed drop-shadow-md">
                    The Future of Technical Interviews. <br />
                    <span className="opacity-80">Powered by AI. Designed for Humans.</span>
                </p>

                <div className="flex flex-col sm:flex-row gap-4 mt-4">
                    <Button
                        size="lg"
                        className="bg-white text-indigo-950 hover:bg-indigo-50 text-lg px-8 py-6 rounded-full font-semibold transition-all hover:scale-105"
                        onClick={() => {
                            const MAIN_URL = process.env.NODE_ENV === 'development' ? 'http://localhost:3000' : 'https://skillscreen.dev';
                            window.location.href = `${MAIN_URL}/signup`;
                        }}
                    >
                        Get Started
                    </Button>
                    <Button
                        size="lg"
                        variant="outline"
                        className="border-white/20 text-white hover:bg-white/10 text-lg px-8 py-6 rounded-full font-semibold backdrop-blur-sm transition-all hover:scale-105"
                        onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}
                    >
                        View Demo
                    </Button>
                </div>
            </div>

            {/* Gradient Overlay for better text readability at the bottom/top if needed */}
            <div className="absolute inset-0 z-10 pointer-events-none" />
        </div>
    )
}
