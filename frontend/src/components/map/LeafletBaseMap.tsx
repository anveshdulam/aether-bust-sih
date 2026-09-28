import React, { useEffect, useState } from 'react';
import { flushSync } from 'react-dom';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import DeckGL from '@deck.gl/react';
import { Layer } from '@deck.gl/core';

interface LeafletBaseMapProps {
  layers: Layer[];
  children?: React.ReactNode;
}

// Map bounds from PRD 0.1
const BOUNDS: [[number, number], [number, number]] = [
  [6.0, 68.0],     // South-West
  [37.75, 99.75]   // North-East
];

// Helper to sync Leaflet to DeckGL synchronously
const DeckGLOverlay = ({ deckLayers }: { deckLayers: Layer[] }) => {
  const map = useMap();
  const [viewState, setViewState] = useState({
    longitude: map.getCenter().lng,
    latitude: map.getCenter().lat,
    zoom: map.getZoom(),
    pitch: 0,
    bearing: 0
  });

  useEffect(() => {
    const onMove = () => {
      flushSync(() => {
        setViewState({
          longitude: map.getCenter().lng,
          latitude: map.getCenter().lat,
          zoom: map.getZoom(),
          pitch: 0,
          bearing: 0
        });
      });
    };
    
    map.on('move', onMove);
    map.on('moveend', onMove);
    map.on('zoom', onMove);
    map.on('zoomend', onMove);
    return () => {
      map.off('move', onMove);
      map.off('moveend', onMove);
      map.off('zoom', onMove);
      map.off('zoomend', onMove);
    };
  }, [map]);

  return (
    <div className="absolute inset-0 pointer-events-none z-[400]">
      <DeckGL
        viewState={viewState}
        layers={deckLayers}
        useDevicePixels={true}
      />
    </div>
  );
};

export const LeafletBaseMap: React.FC<LeafletBaseMapProps> = ({ layers, children }) => {
  return (
    <MapContainer 
      bounds={BOUNDS}
      maxBounds={BOUNDS}
      minZoom={4}
      className="w-full h-full bg-[#0B1220]"
      zoomControl={true}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        className="dark-map-tiles"
      />
      <DeckGLOverlay deckLayers={layers} />
      {children}
    </MapContainer>
  );
};
