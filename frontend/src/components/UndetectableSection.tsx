'use client';

import { motion } from 'framer-motion';
import { Check, X } from 'lucide-react';

export function UndetectableSection() {
  const appLogos = [
    { 
      name: 'Microsoft Teams', 
      logoUrl: '/logos/teams.png',
      color: 'bg-[#6264A7]',
      invert: false,
      fallback: 'T'
    },
    { 
      name: 'Zoom', 
      logoUrl: '/logos/zoom.png',
      color: 'bg-[#2D8CFF]',
      invert: false,
      fallback: 'Z'
    },
    { 
      name: 'Google Meet', 
      logoUrl: '/logos/meet.png',
      color: 'bg-white',
      invert: false,
      fallback: 'G'
    },
    { 
      name: 'Webex', 
      logoUrl: '/logos/webex.svg',
      color: 'bg-[#00B8E5]',
      invert: false,
      fallback: 'W'
    },
  ];

  return (
    <section className="relative py-20 px-4 md:px-8 lg:px-16 bg-transparent">
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4">
            No external meeting software.
            <br />
            Interview directly on SkillScreen.
          </h2>
          <p className="text-lg text-white-600 max-w-3xl mx-auto mb-4">
            Built-in video interviews. No Zoom, Teams, or Meet required. Everything you need in one platform.
          </p>
          <button className="text-blue-600 hover:text-blue-900 text-base font-medium transition-colors underline">
            Why use SkillScreen's native interviewing?
          </button>
        </motion.div>

        {/* Comparison Section with Floating Logos */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="relative bg-gray-50 rounded-3xl p-8 md:p-12 shadow-2xl"
        >
          {/* Floating Logos Around Comparison - Being Pushed Away */}
          {appLogos.map((app, index) => {
            const positions = [
              { top: '-80px', left: '2%', rotation: -25, initialX: 0, initialY: 0, finalX: -40, finalY: -30 },
              { top: '-70px', right: '2%', left: 'auto', rotation: 22, initialX: 0, initialY: 0, finalX: 40, finalY: -25 },
              { bottom: '-80px', left: '3%', top: 'auto', rotation: -20, initialX: 0, initialY: 0, finalX: -35, finalY: 30 },
              { bottom: '-70px', right: '3%', top: 'auto', left: 'auto', rotation: 18, initialX: 0, initialY: 0, finalX: 35, finalY: 30 },
            ];
            const pos = positions[index] || positions[0];
            
            return (
              <motion.div
                key={app.name}
                initial={{ 
                  opacity: 0.4, 
                  scale: 1.1, 
                  x: pos.initialX, 
                  y: pos.initialY,
                  rotate: 0
                }}
                whileInView={{ 
                  opacity: 0.8, 
                  scale: 1, 
                  x: pos.finalX, 
                  y: pos.finalY,
                  rotate: pos.rotation
                }}
                viewport={{ once: true }}
                transition={{ 
                  duration: 0.8, 
                  delay: 0.3 + index * 0.15,
                  type: "spring",
                  stiffness: 80,
                  damping: 12
                }}
                className="absolute hidden md:block z-10"
                style={{
                  top: pos.top,
                  left: pos.left,
                  right: pos.right,
                  bottom: pos.bottom,
                }}
              >
                <div
                  className={`
                    ${app.color}
                    w-20 h-20 lg:w-28 lg:h-28
                    rounded-2xl
                    flex items-center justify-center
                    shadow-[0_10px_30px_rgba(0,0,0,0.25)]
                    border border-white/30
                    p-3 lg:p-4
                    backdrop-blur-sm
                  `}
                >
                  <img
                    src={app.logoUrl}
                    alt={`${app.name} logo`}
                    className="w-full h-full object-contain"
                    style={{ 
                      filter: app.invert ? 'brightness(0) invert(1)' : 'none',
                      maxWidth: '80%',
                      maxHeight: '80%'
                    }}
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      const parent = target.parentElement;
                      if (parent && !parent.querySelector('span')) {
                        const fallback = document.createElement('span');
                        fallback.className = 'text-white text-xl font-bold';
                        fallback.textContent = app.fallback || app.name.charAt(0);
                        parent.appendChild(fallback);
                      }
                    }}
                  />
                </div>
              </motion.div>
            );
          })}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Left: External Platforms */}
            <div className="bg-transparent backdrop-blur-sm rounded-2xl p-6 md:p-8 border-2 border-red-200">
              <h3 className="text-2xl md:text-3xl font-bold text-black mb-4">
                External Meeting Tools
              </h3>
              <div className="flex items-center gap-2 mb-6 text-red-600">
                <X className="w-5 h-5 flex-shrink-0" />
                <span className="text-base md:text-lg font-medium">
                  Requires additional software setup
                </span>
              </div>
              <div className="relative bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl p-6 h-48 md:h-64 flex flex-col items-center justify-center">
                <div className="grid grid-cols-2 gap-3 mb-4">
                  {appLogos.map((app, idx) => (
                    <div key={idx} className={`w-12 h-12 ${app.color} rounded-lg flex items-center justify-center p-2 opacity-60`}>
                      <img
                        src={app.logoUrl}
                        alt={app.name}
                        className="w-full h-full object-contain"
                        style={{ 
                          filter: app.invert ? 'brightness(0) invert(1)' : 'none',
                          maxWidth: '70%',
                          maxHeight: '70%'
                        }}
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          const parent = target.parentElement;
                          if (parent && !parent.querySelector('span')) {
                            const fallback = document.createElement('span');
                            fallback.className = 'text-white text-xs font-bold';
                            fallback.textContent = app.fallback || app.name.charAt(0);
                            parent.appendChild(fallback);
                          }
                        }}
                      />
                    </div>
                  ))}
                </div>
                <p className="text-sm text-gray-600 text-center font-medium">
                  Multiple tools, complex setup, context switching
                </p>
              </div>
            </div>

            {/* Right: SkillScreen */}
            <div className="bg-gradient-to-br from-primary-300 to-primary-200 rounded-2xl p-6 md:p-8 border-2 border-green-200 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center p-1.5">
                  <img src="/logo.png" alt="SkillScreen" className="w-full h-full object-contain" />
                </div>
                <h3 className="text-2xl md:text-3xl font-bold text-white">
                  SkillScreen
                </h3>
              </div>
              <div className="flex items-center gap-2 mb-6 text-white">
                <Check className="w-5 h-5 flex-shrink-0" />
                <span className="text-base md:text-lg font-medium">
                  Built-in video interviews, no external tools
                </span>
              </div>
              <div className="relative bg-white/10 backdrop-blur-sm rounded-xl p-6 h-48 md:h-64 border-2 border-white/20">
                <div className="flex flex-col items-center justify-center h-full space-y-4">
                  <div className="w-20 h-20 bg-white rounded-2xl flex items-center justify-center shadow-lg p-3">
                    <img src="/logo.png" alt="SkillScreen" className="w-full h-full object-contain" />
                  </div>
                  <div className="text-center">
                    <p className="text-white font-semibold text-lg mb-2">All-in-One Platform</p>
                    <p className="text-white/80 text-sm">
                      Video interviews • Code editor • AI analysis
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

