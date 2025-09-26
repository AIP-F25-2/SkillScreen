'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';
import { motion, useScroll, useTransform } from 'framer-motion';
import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';

export default function NavBar() {
  const pathname = usePathname();
  const router = useRouter();
  const { scrollY } = useScroll();
  const [isScrolled, setIsScrolled] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();
  
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

  return (
    <motion.div
      className="fixed top-0 left-1/2 z-50"
      style={navbarStyle}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between h-16">
        {/* Logo */}
        <motion.div style={{ transform: logoTransform }}>
          <Link href="/" className="flex items-center space-x-2">
            <div className="relative w-8 h-8">
              <Image
                src="/logo.png"
                alt="IntervuAI Logo"
                fill
                className="object-contain"
              />
            </div>
            <span className="text-white text-xl font-bold">
              IntervuAI
            </span>
          </Link>
        </motion.div>

        {/* Navigation Links */}
        <div className="flex space-x-4">
          {/* Show dashboard link based on user type */}
          {isAuthenticated && user && (
            <Link
              href={user.userType === 'recruiter' ? '/recruiter' : '/candidate'}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
                isActive(user.userType === 'recruiter' ? '/recruiter' : '/candidate')
                  ? 'bg-white/10 text-white shadow-lg shadow-black/10'
                  : 'text-white/70 hover:bg-white/5 hover:text-white hover:shadow-lg hover:shadow-black/10'
              }`}
            >
              {user.userType === 'recruiter' ? 'Recruiter Dashboard' : 'Candidate Dashboard'}
            </Link>
          )}
          
          {/* Always show contact */}
          <Link
            href="/contact"
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
              isActive('/contact')
                ? 'bg-white/10 text-white shadow-lg shadow-black/10'
                : 'text-white/70 hover:bg-white/5 hover:text-white hover:shadow-lg hover:shadow-black/10'
            }`}
          >
            Contact
          </Link>
        </div>

        {/* User Menu */}
        <motion.div style={{ transform: signOutTransform }} className="flex items-center space-x-4">
          {isAuthenticated && user ? (
            <>
              {/* User Info */}
              <div className="hidden md:flex flex-col items-end">
                <span className="text-white text-sm font-medium">{user.name}</span>
                <span className="text-white/60 text-xs capitalize">{user.userType}</span>
              </div>
              
              {/* User Avatar */}
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">
                  {user.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                </span>
              </div>
              
              {/* Sign Out Button */}
              <button 
                onClick={() => {
                  logout();
                  router.push('/login');
                }}
                className="bg-[#27272A] text-white px-5 py-2 rounded-lg text-sm font-medium transition-all duration-300 hover:bg-[#3F3F46]"
              >
                Sign Out
              </button>
            </>
          ) : (
            /* Sign In Button */
            <button 
              onClick={() => router.push('/login')}
              className="bg-white text-black px-5 py-2 rounded-lg text-sm font-medium transition-all duration-300 hover:bg-white/90"
            >
              Sign In
            </button>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
}