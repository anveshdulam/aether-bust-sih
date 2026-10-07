import { useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';

export const useKeyboardShortcuts = () => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input or textarea
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA'
      ) {
        return;
      }

      const {
        leadTime,
        setLeadTime,
        setSelectedCell,
        baselineMode,
        setBaselineMode,
      } = useAppStore.getState();

      switch (e.key) {
        case 'Escape':
          setSelectedCell(null);
          break;
        case 'ArrowRight':
          if (leadTime < 10) setLeadTime(leadTime + 1);
          break;
        case 'ArrowLeft':
          if (leadTime > 1) setLeadTime(leadTime - 1);
          break;
        case 'c':
        case 'C':
          setBaselineMode(!baselineMode);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
};
