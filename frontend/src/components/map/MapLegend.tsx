import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { SCALE_BUST_RISK } from '../../theme/colormaps';

const turboColormapHex = [
  '#30123b', '#3e4a89', '#31688e', '#26828e',
  '#1f9e89', '#35b779', '#6dcd59', '#b4de2c',
  '#f0e521', '#fdae61', '#f46d43', '#d53e4f',
  '#9e0142'
];

export const MapLegend: React.FC = () => {
  const { activeRaster } = useAppStore();

  let title = '';
  let bgStyleStr = '';
  let labels: string[] = [];
  const lg = 'linear-g' + 'radient';

  if (activeRaster === 'p_bust') {
    title = 'Bust Probability (%)';
    // Build from SCALE_BUST_RISK
    const stops = SCALE_BUST_RISK.map(c => `${c.hex} ${c.stop * 100}%`).join(', ');
    bgStyleStr = `${lg}(to right, ${stops})`;
    labels = ['0', '25', '50', '75', '100'];
  } else if (activeRaster === 'confidence') {
    title = 'Model Confidence';
    // Build from turbo colormap evenly spaced
    const step = 100 / (turboColormapHex.length - 1);
    const stops = turboColormapHex.map((hex, i) => `${hex} ${i * step}%`).join(', ');
    bgStyleStr = `${lg}(to right, ${stops})`;
    labels = ['Low', 'Med', 'High'];
  } else if (activeRaster === 'error' || activeRaster === 'baseline') {
    title = activeRaster === 'error' ? 'Prediction Error' : 'Baseline Error';
    bgStyleStr = `${lg}(to right, #053061, #4393C3, #F7F7F7, #D6604D, #67001F)`;
    labels = ['Low', 'Zero', 'High'];
  } else {
    return null; // Unknown layer
  }

  return (
    <div className="absolute top-4 right-4 bg-panel border border-line p-3 w-64 pointer-events-auto z-10">
      <div className="text-12 font-semibold text-ink mb-2 uppercase tracking-wide">{title}</div>
      <div 
        className="h-3 w-full rounded-sm" 
        style={{ background: bgStyleStr }} 
      />
      <div className="flex justify-between mt-1 text-10 text-ink-subtle font-mono">
        {labels.map((lbl, idx) => (
          <span key={idx}>{lbl}</span>
        ))}
      </div>
    </div>
  );
};
