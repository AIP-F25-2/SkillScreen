'use client';

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface CheatPreventionContextType {
  isActive: boolean;
  violations: string[];
  enableProtection: () => void;
  disableProtection: () => void;
}

const CheatPreventionContext = createContext<CheatPreventionContextType | undefined>(undefined);

export function CheatPreventionProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [isActive, setIsActive] = useState(false);
  const [violations, setViolations] = useState<string[]>([]);
  const [hasReloaded, setHasReloaded] = useState(false);

  const addViolation = useCallback((violation: string) => {
    setViolations((prev) => [...prev, `${new Date().toISOString()}: ${violation}`]);
  }, []);

  // Prevent page refresh/reload
  useEffect(() => {
    if (!isActive) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = 'Your interview progress will be lost if you leave or reload this page.';
      addViolation('Attempted to reload/leave page');
      return e.returnValue;
    };

    const handleUnload = () => {
      // Mark that user attempted to reload
      sessionStorage.setItem('interview_violation_reload', 'true');
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('unload', handleUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('unload', handleUnload);
    };
  }, [isActive, addViolation]);

  // Check if page was reloaded during active interview
  useEffect(() => {
    if (!isActive) return;

    const wasReloaded = sessionStorage.getItem('interview_violation_reload');
    if (wasReloaded === 'true' && !hasReloaded) {
      setHasReloaded(true);
      addViolation('Page was reloaded - CRITICAL VIOLATION');
      
      // Clear the flag
      sessionStorage.removeItem('interview_violation_reload');
      
      // Optionally: Force end interview
      setTimeout(() => {
        alert('Interview terminated: Page reload detected. This is a violation of interview rules.');
        router.push('/');
      }, 100);
    }
  }, [isActive, hasReloaded, addViolation, router]);

  // Prevent copy/paste
  useEffect(() => {
    if (!isActive) return;

    const preventCopy = (e: ClipboardEvent) => {
      // Allow copy in specific elements (like code editor)
      const target = e.target as HTMLElement;
      if (target.closest('[data-allow-copy="true"]')) {
        return; // Allow copy in code editor
      }
      
      e.preventDefault();
      addViolation('Attempted to copy content');
    };

    const preventPaste = (e: ClipboardEvent) => {
      // Allow paste in specific elements (like code editor)
      const target = e.target as HTMLElement;
      if (target.closest('[data-allow-paste="true"]')) {
        return; // Allow paste in code editor
      }
      
      e.preventDefault();
      addViolation('Attempted to paste content');
    };

    const preventCut = (e: ClipboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.closest('[data-allow-cut="true"]')) {
        return;
      }
      
      e.preventDefault();
      addViolation('Attempted to cut content');
    };

    document.addEventListener('copy', preventCopy);
    document.addEventListener('paste', preventPaste);
    document.addEventListener('cut', preventCut);

    return () => {
      document.removeEventListener('copy', preventCopy);
      document.removeEventListener('paste', preventPaste);
      document.removeEventListener('cut', preventCut);
    };
  }, [isActive, addViolation]);

  // Detect tab switching / window blur
  useEffect(() => {
    if (!isActive) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        addViolation('Tab switched or window minimized');
      }
    };

    const handleBlur = () => {
      addViolation('Window lost focus');
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleBlur);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleBlur);
    };
  }, [isActive, addViolation]);

  // Prevent right-click context menu
  useEffect(() => {
    if (!isActive) return;

    const preventContextMenu = (e: MouseEvent) => {
      e.preventDefault();
      addViolation('Attempted to open context menu');
    };

    document.addEventListener('contextmenu', preventContextMenu);

    return () => {
      document.removeEventListener('contextmenu', preventContextMenu);
    };
  }, [isActive, addViolation]);

  // Prevent keyboard shortcuts
  useEffect(() => {
    if (!isActive) return;

    const preventKeyboardShortcuts = (e: KeyboardEvent) => {
      // Prevent F12, Ctrl+Shift+I, Ctrl+Shift+J (DevTools)
      if (
        e.key === 'F12' ||
        (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) ||
        (e.metaKey && e.altKey && (e.key === 'I' || e.key === 'J' || e.key === 'C'))
      ) {
        e.preventDefault();
        addViolation('Attempted to open developer tools');
        return;
      }

      // Prevent Ctrl+U (View Source)
      if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        addViolation('Attempted to view page source');
        return;
      }

      // Prevent Ctrl+S (Save Page)
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        addViolation('Attempted to save page');
        return;
      }

      // Prevent Ctrl+P (Print)
      if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        addViolation('Attempted to print page');
        return;
      }

      // Prevent Ctrl+A (Select All) outside code editor
      const target = e.target as HTMLElement;
      if ((e.ctrlKey || e.metaKey) && e.key === 'a' && !target.closest('[data-allow-select="true"]')) {
        e.preventDefault();
        addViolation('Attempted to select all content');
        return;
      }
    };

    document.addEventListener('keydown', preventKeyboardShortcuts);

    return () => {
      document.removeEventListener('keydown', preventKeyboardShortcuts);
    };
  }, [isActive, addViolation]);

  // Fullscreen recommendation (optional, not enforced)
  useEffect(() => {
    if (!isActive) return;

    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) {
        // User exited fullscreen - just log, don't force
        addViolation('Exited fullscreen mode');
      }
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, [isActive, addViolation]);

  const enableProtection = useCallback(() => {
    setIsActive(true);
    setViolations([]);
    // Mark session as active
    sessionStorage.setItem('interview_active', 'true');
  }, []);

  const disableProtection = useCallback(() => {
    setIsActive(false);
    sessionStorage.removeItem('interview_active');
    sessionStorage.removeItem('interview_violation_reload');
  }, []);

  const value: CheatPreventionContextType = {
    isActive,
    violations,
    enableProtection,
    disableProtection,
  };

  return (
    <CheatPreventionContext.Provider value={value}>
      {children}
    </CheatPreventionContext.Provider>
  );
}

export function useCheatPrevention() {
  const context = useContext(CheatPreventionContext);
  if (context === undefined) {
    throw new Error('useCheatPrevention must be used within a CheatPreventionProvider');
  }
  return context;
}

