import React, { useEffect, useRef } from 'react';
import { SCALE_BUST_RISK } from '../../theme/colormaps';
import { createColorScale } from '../../utils/colorScale';

interface GradcamThumbProps {
  gradcam: number[][]; // 128x128
}

const scale = createColorScale(SCALE_BUST_RISK, 1);

export const GradcamThumb: React.FC<GradcamThumbProps> = ({ gradcam }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || !gradcam || gradcam.length !== 128) return;
    
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    const imgData = ctx.createImageData(128, 128);
    for (let i = 0; i < 128; i++) {
      for (let j = 0; j < 128; j++) {
        const val = gradcam[i]?.[j] || 0;
        const idx = (i * 128 + j) * 4;
        const [r, g, b, a] = scale(val);
        imgData.data[idx] = r;
        imgData.data[idx + 1] = g;
        imgData.data[idx + 2] = b;
        imgData.data[idx + 3] = a * 255;
      }
    }
    ctx.putImageData(imgData, 0, 0);
  }, [gradcam]);

  return (
    <div className="w-full aspect-square bg-bg-inset border border-border-subtle rounded-sm overflow-hidden flex items-center justify-center">
      {gradcam ? (
        <canvas ref={canvasRef} width={128} height={128} className="w-full h-full object-cover rendering-pixelated" />
      ) : (
        <span className="text-xs text-text-muted">No spatial data</span>
      )}
    </div>
  );
};
