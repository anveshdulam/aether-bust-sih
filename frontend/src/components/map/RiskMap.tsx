import React, { useMemo } from 'react';
import { useConsoleStore } from '../../store/useConsoleStore';
import { useConfidenceMap, useBustProbability, useBustDetections } from '../../api/queries';
import { LeafletBaseMap } from './LeafletBaseMap';
import { createDeckGridLayer } from './DeckGridLayer';
import { createBustPolygonLayer } from './BustPolygonLayer';
import { SCALE_CONFIDENCE, SCALE_BUST_RISK } from '../../theme/colormaps';
import { ScrubberBar } from './ScrubberBar';

export const RiskMap: React.FC = () => {
  const { runId, layer, leadTime, opacity } = useConsoleStore();

  const { data: confData } = useConfidenceMap(runId, leadTime);
  const { data: bustData } = useBustProbability(layer === 'p_bust' ? { run_id: runId || '' } : null);
  const { data: detections } = useBustDetections(runId);

  const deckLayers = useMemo(() => {
    const layers = [];
    
    if (layer === 'confidence' && confData) {
      const deckLyr = createDeckGridLayer(
        'confidence-layer',
        confData.grid,
        confData.values,
        SCALE_CONFIDENCE,
        opacity,
        100 // domain max
      );
      if (deckLyr) layers.push(deckLyr);
    }
    
    if (layer === 'p_bust' && bustData) {
      const activeLayerData = bustData.layers.find(l => l.lead_time === leadTime);
      if (activeLayerData) {
        const deckLyr = createDeckGridLayer(
          'bust-layer',
          bustData.grid,
          activeLayerData.values,
          SCALE_BUST_RISK,
          opacity,
          1 // domain max
        );
        if (deckLyr) layers.push(deckLyr);
      }
    }

    if (detections && detections.length > 0) {
      const activeDets = detections.filter(d => d.lead_time === leadTime);
      const polyLyr = createBustPolygonLayer('bust-polygons', activeDets, opacity);
      if (polyLyr) layers.push(polyLyr);
    }

    return layers;
  }, [layer, confData, bustData, detections, leadTime, opacity]);

  return (
    <div className="relative w-full h-full flex flex-col">
      <div className="flex-1 relative">
        <LeafletBaseMap layers={deckLayers} />
      </div>
      <div className="shrink-0 p-4 bg-bg-panel border-t border-border-subtle">
        <ScrubberBar />
      </div>
    </div>
  );
};
