// ParticlesBackground.tsx
import { useEffect } from 'react';

const ParticlesBackground: React.FC = () => {
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).particlesJS.load('particles-js', '/particles-config.json', () => {
        console.log('particles.js loaded');
      });
    }
    return () => {
      if ((window as any).pJSDom?.length) {
        const canvas = document.getElementById('particles-js')?.querySelector('canvas');
        if (canvas) canvas.remove();
        (window as any).pJSDom = [];
      }
    };
  }, []);

  return <div id="particles-js" />;
};

export default ParticlesBackground;