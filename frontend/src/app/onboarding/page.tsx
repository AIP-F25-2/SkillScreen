'use client';

import { useState, useEffect, ChangeEvent } from 'react';
import { ShaderAnimation } from '@/components/ui/shader-lines';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import Footer from '@/components/Footer';

type UserType = 'recruiter' | '';

interface OnboardingFormData {
  // Common fields
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  // Recruiter specific fields
  company?: string;
  domain?: string;
  role?: string;
  teamSize?: string;
  industry?: string;
  // Job seeker specific fields
  experience: string;
  skills: string;
  education: string;
  preferredRole: string;
  availability: string;
}

interface Errors {
  userType?: string;
  firstName?: string;
  lastName?: string;
  email?: string;
  password?: string;
  company?: string;
  domain?: string;
  role?: string;
  industry?: string;
  experience?: string;
  skills?: string;
  preferredRole?: string;
  submit?: string;
}

export default function Onboarding() {
  const router = useRouter();
  const { register, isAuthenticated } = useAuth();
  const [step, setStep] = useState(1);
  const [userType, setUserType] = useState<UserType>('');
  const [rippleEffect, setRippleEffect] = useState(false);
  const [textAnimation, setTextAnimation] = useState(false);
  const [showWelcome, setShowWelcome] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [formData, setFormData] = useState<OnboardingFormData>({
    // Common fields
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    // Recruiter specific fields
    company: '',
    domain: '',
    // Job seeker specific fields
    experience: '',
    skills: '',
    education: '',
    preferredRole: '',
    availability: '',
  });
  const [permissions, setPermissions] = useState({
    camera: false,
    microphone: false,
  });
  const [errors, setErrors] = useState<Errors>({});

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const requestMediaPermissions = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setPermissions({
        camera: true,
        microphone: true,
      });
      stream.getTracks().forEach(track => track.stop());
    } catch (error) {
      console.error('Error requesting permissions:', error);
    }
  };

  const validateStep = () => {
    const newErrors: Errors = {};

    if (step === 1 && !userType) {
      newErrors.userType = 'Please select your role';
    }

    if (step === 2) {
      if (!formData.firstName) newErrors.firstName = 'First name is required';
      if (!formData.lastName) newErrors.lastName = 'Last name is required';
      if (!formData.email) newErrors.email = 'Email is required';
      else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Email is invalid';
      if (!formData.password) newErrors.password = 'Password is required';
      else if (formData.password.length < 6) newErrors.password = 'Password must be at least 6 characters';

      if (userType === 'recruiter') {
        if (!formData.company) newErrors.company = 'Company name is required';
        if (!formData.domain) newErrors.domain = 'Domain is required';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = async () => {
    if (!validateStep()) return;

    if (step === 2) {
      // Final step - register user and complete onboarding
      setIsRegistering(true);
      setRippleEffect(true);
      setTimeout(() => setRippleEffect(false), 1000);

      try {
        // Register the user
        const result = await register({
          firstName: formData.firstName,
          lastName: formData.lastName,
          email: formData.email,
          password: formData.password,
          userType: 'recruiter',
          company: formData.company,
          domain: formData.domain
        });

        if (result.success) {
          // Start welcome sequence during ripple
          setTimeout(() => {
            setIsRegistering(false);
            setShowWelcome(true);
          }, 800);
        } else {
          setIsRegistering(false);
          setErrors({ submit: result.error || 'Registration failed' });
        }
      } catch (error) {
        setIsRegistering(false);
        setErrors({ submit: 'Registration failed. Please try again.' });
      }
    } else {
      // Regular steps - trigger ripple effect
      setRippleEffect(true);

      // Reset ripple effect after animation
      setTimeout(() => {
        setRippleEffect(false);
      }, 1200); // Match ripple duration

      if (step < 2) {
        setStep(prev => prev + 1);
      }
    }
  };

  const handleContinueToDashboard = () => {
    setIsTransitioning(true);
    // Add a longer delay for smooth fade out, then navigate
    setTimeout(() => {
      router.push('/login');
    }, 800);
  };

  // Auto-transition after 5 seconds
  useEffect(() => {
    if (showWelcome && !isTransitioning) {
      const timer = setTimeout(() => {
        handleContinueToDashboard();
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [showWelcome, isTransitioning, userType]);

  const handleBack = () => {
    if (step > 1) {
      setStep(prev => prev - 1);
      setErrors({});
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-8 text-center">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">Welcome to IntervuAI</h2>
            <p className="text-lg text-white/80 mb-8">Let's get started! Are you a...</p>
            <div className="flex flex-col sm:flex-row justify-center gap-6">
              <button
                onClick={() => setUserType('recruiter')}
                className={`px-8 py-4 rounded-xl transition-all duration-300 transform hover:scale-105 ${userType === 'recruiter'
                  ? 'bg-white text-black'
                  : 'bg-white/10 hover:bg-white/20 text-white'
                  }`}
              >
                Recruiter / Employer
              </button>
            </div>
            {errors.userType && (
              <p className="text-red-400 text-sm mt-2">{errors.userType}</p>
            )}
          </div>
        );

      case 2:
        return (
          <div className="bg-black/40 backdrop-blur-md rounded-2xl p-8 md:p-12 w-full max-w-2xl mx-auto shadow-2xl">
            <h2 className="text-3xl font-bold text-white mb-6 text-center">
              Tell us about your company
            </h2>
            <div className="space-y-4">
              {/* Common Fields */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <input
                    type="text"
                    name="firstName"
                    placeholder="First Name"
                    value={formData.firstName}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 bg-white/10 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
                  />
                  {errors.firstName && (
                    <p className="text-red-400 text-sm">{errors.firstName}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <input
                    type="text"
                    name="lastName"
                    placeholder="Last Name"
                    value={formData.lastName}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 bg-white/10 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
                  />
                  {errors.lastName && (
                    <p className="text-red-400 text-sm">{errors.lastName}</p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <input
                  type="email"
                  name="email"
                  placeholder="Email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-white/10 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
                />
                {errors.email && (
                  <p className="text-red-400 text-sm">{errors.email}</p>
                )}
              </div>

              <div className="space-y-2">
                <input
                  type="password"
                  name="password"
                  placeholder="Create a password (min. 6 characters)"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-white/10 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
                />
                {errors.password && (
                  <p className="text-red-400 text-sm">{errors.password}</p>
                )}
              </div>

              {/* Recruiter Specific Fields */}
              <div className="space-y-2">
                <input
                  type="text"
                  name="company"
                  placeholder="Company Name"
                  value={formData.company}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-white/10 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
                />
                {errors.company && (
                  <p className="text-red-400 text-sm">{errors.company}</p>
                )}
                <div className="space-y-2">
                  <input
                    type="text"
                    name="domain"
                    placeholder="Company Domain (e.g. nvidia.ai)"
                    value={formData.domain}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 bg-white/10 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30"
                  />
                  {errors.domain && (
                    <p className="text-red-400 text-sm">{errors.domain}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        );


      default:
        return null;
    }
  };

  const renderNavigation = () => (
    <div className="mt-8 border-t border-white/10 pt-8">
      <div className="flex justify-between items-center">
        <div className="flex gap-3">
          {[1, 2].map((i) => (
            <div key={i} className="flex flex-col items-center">
              <div
                className={`w-3 h-3 rounded-full transition-all duration-300 ${step === i
                  ? 'bg-white scale-125'
                  : step > i
                    ? 'bg-green-500'
                    : 'bg-white/30'
                  }`}
              />
              <div className="h-1 w-16 bg-white/10 mt-2 rounded-full overflow-hidden">
                <div
                  className={`h-full bg-white transition-all duration-500 ${step > i
                    ? 'w-full'
                    : step === i
                      ? 'w-1/2'
                      : 'w-0'
                    }`}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-4">
          {step > 1 && (
            <button
              onClick={handleBack}
              className="px-6 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-white transition-all duration-300 flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
              Back
            </button>
          )}
          {step <= 2 && (
            <button
              onClick={handleNext}
              disabled={(step === 1 && !userType) || isRegistering}
              className={`px-6 py-2 rounded-xl transition-all duration-300 flex items-center gap-2 ${(step === 1 && !userType) || isRegistering
                ? 'bg-white/10 text-white/50 cursor-not-allowed'
                : 'bg-white text-black hover:bg-white/90'
                }`}
            >
              {isRegistering ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-black"></div>
                  Creating Account...
                </>
              ) : (
                <>
                  {step === 2 ? 'Complete' : 'Next'}
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <>
      <ShaderAnimation
        currentStep={step}
        totalSteps={2}
        progress={
          step === 1
            ? userType ? 0.5 : 0
            : step === 2
              ? formData.firstName && formData.lastName && formData.email && formData.password ? 0.75 : 0.5
              : 0
        }
        rippleEffect={rippleEffect}
        textAnimation={textAnimation}
        isCompleteRipple={step === 2 && rippleEffect}
        fadeOut={showWelcome}
      />

      {/* Transition Overlay - Full screen fade */}
      <AnimatePresence>
        {isTransitioning && (
          <motion.div
            className="fixed inset-0 bg-black z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, ease: "easeInOut" }}
          />
        )}
      </AnimatePresence>

      {/* Shader Fade Overlay */}
      <AnimatePresence>
        {showWelcome && (
          <motion.div
            className="fixed inset-0 bg-black z-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: isTransitioning ? 0 : 0.8 }}
            transition={{ duration: isTransitioning ? 0.5 : 1.5, ease: "easeInOut" }}
          />
        )}
      </AnimatePresence>

      {/* Onboarding Modal */}
      <AnimatePresence>
        {!showWelcome && (
          <motion.div
            className="relative min-h-screen flex items-center justify-center p-6"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="relative z-10 w-full max-w-4xl bg-black/40 backdrop-blur-md rounded-2xl p-8 md:p-12 shadow-2xl">
              {renderStep()}
              {renderNavigation()}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Expanding Modal Overlay for Complete */}
      <AnimatePresence>
        {showWelcome && (
          <motion.div
            className="fixed inset-0 bg-black/60 backdrop-blur-lg z-15"
            initial={{
              scale: 0.1,
              borderRadius: "1rem",
              x: "50%",
              y: "50%",
              translateX: "-50%",
              translateY: "-50%"
            }}
            animate={{
              scale: isTransitioning ? 1.1 : 1,
              borderRadius: "0rem",
              x: "0%",
              y: "0%",
              translateX: "0%",
              translateY: "0%",
              opacity: isTransitioning ? 0 : 1
            }}
            transition={{
              duration: isTransitioning ? 0.5 : 1.0,
              ease: [0.25, 0.1, 0.25, 1]
            }}
          />
        )}
      </AnimatePresence>

      {/* Welcome Text and Button */}
      <AnimatePresence>
        {showWelcome && (
          <motion.div
            className="fixed inset-0 flex flex-col justify-center items-center p-6 z-30 pointer-events-none"
            initial={{ opacity: 0 }}
            animate={{ opacity: isTransitioning ? 0 : 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            {/* Main Text Container */}
            <div className="flex flex-col items-center justify-center flex-1 max-w-7xl mx-auto">
              <div className="text-center">
                {/* Smaller "Welcome To" text */}
                <motion.div
                  className="text-white text-3xl md:text-4xl lg:text-5xl tracking-[0.2em] leading-none mb-6"
                  style={{
                    fontFamily: 'Korataki, system-ui, sans-serif',
                    fontWeight: 800,
                    textShadow: '0 0 20px rgba(255,255,255,0.3)'
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{
                    duration: 1.0,
                    delay: 0.5,
                    ease: [0.25, 0.1, 0.25, 1]
                  }}
                >
                  WELCOME TO
                </motion.div>

                {/* Large centered "IntervuAI" text */}
                <motion.div
                  className="text-white text-6xl md:text-8xl lg:text-9xl tracking-[0.2em] leading-none"
                  style={{
                    fontFamily: 'Korataki, system-ui, sans-serif',
                    fontWeight: 800,
                    textShadow: '0 0 30px rgba(255,255,255,0.3)'
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{
                    duration: 1.0,
                    delay: 1.5,
                    ease: [0.25, 0.1, 0.25, 1]
                  }}
                >
                  SkillScreen
                </motion.div>
              </div>
            </div>

            {/* Button at bottom */}
            <div className="w-full flex justify-center pb-12">
              <motion.button
                onClick={handleContinueToDashboard}
                className="px-12 py-4 bg-white text-black rounded-full text-lg font-medium hover:bg-white/90 transition-all duration-300 transform hover:scale-105 pointer-events-auto"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.8,
                  delay: 1.5,
                  ease: [0.25, 0.1, 0.25, 1]
                }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Continue to Login →
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <Footer />
    </>
  );
}
