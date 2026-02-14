'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';
import { motion, useScroll, useTransform } from 'framer-motion';
import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { FRONTEND_URL } from '@/lib/config';

interface NavBarProps {
  readonly isPortfolio?: boolean;
}

export default function NavBar({ isPortfolio = false }: NavBarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { scrollY } = useScroll();
  const [isScrolled, setIsScrolled] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();

  const MAIN_URL = FRONTEND_URL;

  const getLinkUrl = (path: string) => {
    if (isPortfolio) {
      return `${MAIN_URL}${path}`;
    }
    return path;
  };

  const handleNavigation = (path: string) => {
    const navigate = isPortfolio
      ? (p: string) => { globalThis.location.href = `${MAIN_URL}${p}`; }
      : (p: string) => { router.push(p); };

    navigate(path);
  };

  const isActive = (path: string) => pathname === path;

  const initialState = {
    background: "rgba(18, 18, 18, 0)",
    width: "100%",
    maxWidth: "1400px",
    borderRadius: "0px",
    backdropFilter: "none",
    border: "none",
    x: "-50%",
    y: "0px",
    scale: 1,
    padding: "0 2rem"
  };

  const scrolledState = {
    background: "rgba(18, 18, 18, 0.7)",
    width: "90%",
    maxWidth: "1400px",
    borderRadius: "16px",
    backdropFilter: "blur(12px)",
    border: "1px solid rgba(255, 255, 255, 0.1)",
    x: "-50%",
    y: "0.5rem",
    scale: 0.98,
    padding: "0 1.5rem"
  };

  const navbarStyle = {
    background: useTransform(
      scrollY,
      [0, 100],
      [initialState.background, scrolledState.background]
    ),
    width: useTransform(
      scrollY,
      [0, 100],
      [initialState.width, scrolledState.width]
    ),
    maxWidth: initialState.maxWidth,
    borderRadius: useTransform(
      scrollY,
      [0, 100],
      [initialState.borderRadius, scrolledState.borderRadius]
    ),
    backdropFilter: useTransform(
      scrollY,
      [0, 100],
      [initialState.backdropFilter, scrolledState.backdropFilter]
    ),
    border: useTransform(
      scrollY,
      [0, 100],
      [initialState.border, scrolledState.border]
    ),
    x: useTransform(
      scrollY,
      [0, 100],
      [initialState.x, scrolledState.x]
    ),
    y: useTransform(
      scrollY,
      [0, 100],
      [initialState.y, scrolledState.y]
    ),
    scale: useTransform(
      scrollY,
      [0, 100],
      [initialState.scale, scrolledState.scale]
    ),
    padding: useTransform(
      scrollY,
      [0, 100],
      [initialState.padding, scrolledState.padding]
    )
  };

  const logoTransform = useTransform(
    scrollY,
    [0, 100],
    ["translateX(0px)", "translateX(24px)"]
  );

  const signOutTransform = useTransform(
    scrollY,
    [0, 100],
    ["translateX(0px)", "translateX(-24px)"]
  );

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // ... existing code ...
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // ... existing code ...

  return (
    <motion.div
      className="fixed top-0 left-1/2 z-50"
      style={navbarStyle}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between h-16 relative">
        {/* Logo */}
        <motion.div style={{ transform: logoTransform }}>
          <Link href={getLinkUrl("/")} className="flex items-center space-x-2">
            <div className="relative w-8 h-8">
              <Image
                src="/logo.png"
                alt="IntervuAI Logo"
                fill
                sizes="(max-width: 768px) 32px, (max-width: 1200px) 32px, 32px"
                className="object-contain"
              />
            </div>
            <span className="text-white text-xl font-bold">
              SkillScreen
            </span>
          </Link>
        </motion.div>

        {/* Mobile Hamburger Button */}
        <div className="md:hidden">
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="text-white p-2 focus:outline-none"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              {isMobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Right: Nav Links + User Menu (Desktop) */}
        <motion.div style={{ transform: signOutTransform }} className="hidden md:flex items-center space-x-4 ml-auto">
          {/* Navigation Links */}
          <div className="flex items-center space-x-2 mr-2">
            {/* Show dashboard link based on user type */}
            {isAuthenticated && user && (
              (() => {
                const dashboardPath = user.userType === 'recruiter' ? '/recruiter' : '/candidate';
                const dashboardText = user.userType === 'recruiter' ? 'Recruiter Dashboard' : 'Candidate Dashboard';
                return (
                  <Link
                    href={getLinkUrl(dashboardPath)}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${isActive(dashboardPath)
                      ? 'bg-white/10 text-white shadow-lg shadow-black/10'
                      : 'text-white/70 hover:bg-white/5 hover:text-white hover:shadow-lg hover:shadow-black/10'
                      }`}
                  >
                    {dashboardText}
                  </Link>
                );
              })()
            )}

            {/* Contact */}
            <Link
              href={getLinkUrl("/contact")}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${isActive('/contact')
                ? 'bg-white/10 text-white shadow-lg shadow-black/10'
                : 'text-white/70 hover:bg-white/5 hover:text-white hover:shadow-lg hover:shadow-black/10'
                }`}
            >
              Contact
            </Link>

            {/* About */}
            <Link
              href={getLinkUrl("/about")}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${isActive('/about')
                ? 'bg-white/10 text-white shadow-lg shadow-black/10'
                : 'text-white/70 hover:bg-white/5 hover:text-white hover:shadow-lg hover:shadow-black/10'
                }`}
            >
              About
            </Link>
          </div>
          <button
            onClick={() => handleNavigation('/interview-setup')}
            className="bg-white text-black px-5 py-2 rounded-lg text-sm font-medium transition-all duration-300 hover:bg-white/90"
          >
            Join Meeting
          </button>
          {/* User Menu */}
          {isAuthenticated && user ? (
            <>
              {/* User Info */}
              <div className="flex flex-col items-end">
                <span className="text-white text-sm font-medium">{user.name}</span>
                <span className="text-white/60 text-xs capitalize">{user.userType}</span>
              </div>

              {/* User Avatar */}
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">
                  {user.name.split(' ').map((n: string) => n[0]).join('').toUpperCase()}
                </span>
              </div>

              {/* Sign Out Button */}
              <button
                onClick={() => {
                  logout();
                  handleNavigation('/login');
                }}
                className="bg-[#27272A] text-white px-5 py-2 rounded-lg text-sm font-medium transition-all duration-300 hover:bg-[#3F3F46]"
              >
                Sign Out
              </button>
            </>
          ) : (
            /* Auth CTA Buttons */
            <div className="flex items-center space-x-3">
              <button
                onClick={() => handleNavigation('/onboarding')}
                className="px-5 py-2 rounded-lg text-sm font-medium transition-all duration-300 bg-white/10 text-white hover:bg-white/20"
              >
                Sign Up
              </button>
              <button
                onClick={() => handleNavigation('/login')}
                className="bg-white text-black px-5 py-2 rounded-lg text-sm font-medium transition-all duration-300 hover:bg-white/90"
              >
                Sign In
              </button>
            </div>
          )}
        </motion.div>
      </div >

      {/* Mobile Menu Dropdown */}
      {
        isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="md:hidden absolute top-16 left-0 w-full bg-[#1a1a1a] border border-white/10 rounded-b-2xl p-4 flex flex-col space-y-4 shadow-xl"
          >
            {isAuthenticated && user && (
              <Link
                href={getLinkUrl(user.userType === 'recruiter' ? '/recruiter' : '/candidate')}
                className="text-white/80 hover:text-white py-2"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {user.userType === 'recruiter' ? 'Recruiter Dashboard' : 'Candidate Dashboard'}
              </Link>
            )}
            <Link href={getLinkUrl("/contact")} className="text-white/80 hover:text-white py-2" onClick={() => setIsMobileMenuOpen(false)}>Contact</Link>
            <Link href={getLinkUrl("/about")} className="text-white/80 hover:text-white py-2" onClick={() => setIsMobileMenuOpen(false)}>About</Link>
            <button
              onClick={() => {
                handleNavigation('/interview-setup');
                setIsMobileMenuOpen(false);
              }}
              className="bg-white text-black px-5 py-2 rounded-lg text-sm font-medium w-full"
            >
              Join Meeting
            </button>

            {isAuthenticated && user ? (
              <div className="pt-4 border-t border-white/10 flex flex-col space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-bold">
                      {user.name.split(' ').map((n: string) => n[0]).join('').toUpperCase()}
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-white text-sm font-medium">{user.name}</span>
                    <span className="text-white/60 text-xs capitalize">{user.userType}</span>
                  </div>
                </div>
                <button
                  onClick={() => {
                    logout();
                    handleNavigation('/login');
                    setIsMobileMenuOpen(false);
                  }}
                  className="bg-[#27272A] text-white px-5 py-2 rounded-lg text-sm font-medium w-full"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="pt-4 border-t border-white/10 flex flex-col space-y-3">
                <button
                  onClick={() => {
                    handleNavigation('/onboarding');
                    setIsMobileMenuOpen(false);
                  }}
                  className="px-5 py-2 rounded-lg text-sm font-medium bg-white/10 text-white w-full"
                >
                  Sign Up
                </button>
                <button
                  onClick={() => {
                    handleNavigation('/login');
                    setIsMobileMenuOpen(false);
                  }}
                  className="bg-white text-black px-5 py-2 rounded-lg text-sm font-medium w-full"
                >
                  Sign In
                </button>
              </div>
            )}
          </motion.div>
        )
      }
    </motion.div >
  );
}