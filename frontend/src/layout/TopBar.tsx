import React, { useEffect, useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { useHealth, useRuns, useBustDetections } from '../api/queries';
import { StatusDot } from '../components/common/StatusDot';
import { AlertCircle, Download, HelpCircle } from 'lucide-react';
import { FlyToInterpolator } from '@deck.gl/core';
import { useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { AttributionResponse } from '../api/types';

export const TopBar: React.FC = () => {
  const [time, setTime] = useState(new Date());
  const queryClient = useQueryClient();
  
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const { data: health } = useHealth();
  const { data: runs } = useRuns();
  const { runId, setRunId, leadTime, setViewState, setSelectedCell, variable } = useAppStore();

  const activeRun = runs?.find(r => r.run_id === runId);
  
  useEffect(() => {
    if (!runId && runs && runs.length > 0) {
      setRunId(runs[0].run_id);
    }
  }, [runs, runId, setRunId]);

  // Compute alert from data
  const { data: detections } = useBustDetections(runId, leadTime);
  const highRiskRegions = detections?.filter(d => d.peak_probability >= 0.8) || [];
  
  // PRE-FETCH ATTRIBUTION: eagerly compute XAI for the worst region in the background
  useEffect(() => {
    if (highRiskRegions.length > 0 && runId) {
      const worst = highRiskRegions.reduce((prev, current) => (prev.peak_probability > current.peak_probability) ? prev : current);
      const lon = (worst.bbox[0] + worst.bbox[2]) / 2;
      const lat = (worst.bbox[1] + worst.bbox[3]) / 2;
      
      queryClient.prefetchQuery({
        queryKey: ['attribution', runId, variable, leadTime, lat, lon],
        queryFn: async () => {
          const res = await apiClient.get<AttributionResponse>('/attribution', {
            params: { run_id: runId, variable, lead_time: leadTime, lat, lon }
          });
          return res.data;
        }
      });
    }
  }, [highRiskRegions, runId, leadTime, variable, queryClient]);

  const handleAlertClick = () => {
    if (highRiskRegions.length > 0) {
      const worst = highRiskRegions.reduce((prev, current) => (prev.peak_probability > current.peak_probability) ? prev : current);
      const lon = (worst.bbox[0] + worst.bbox[2]) / 2;
      const lat = (worst.bbox[1] + worst.bbox[3]) / 2;
      
      setViewState({
        longitude: lon,
        latitude: lat,
        zoom: 7,
        pitch: 0,
        bearing: 0,
        transitionDuration: 1500,
        transitionInterpolator: new FlyToInterpolator()
      });
      
      setSelectedCell([lat, lon]);
    }
  };

  // Compute Valid Time (Init + leadTime days)
  const validTime = activeRun ? new Date(new Date(activeRun.init_time).getTime() + leadTime * 24 * 60 * 60 * 1000) : new Date();

  return (
    <div className="h-14 bg-bg-panel border-b border-border flex items-center justify-between px-4 shrink-0 shadow-none z-20">
      
      {/* Left: Wordmark, Run Selector, Badge */}
      <div className="flex items-center gap-4 flex-1">
        <div className="font-bold text-[15px] tracking-wide text-text-primary">
          <span className="text-accent">AETHER</span>-BUST
        </div>
        
        <div className="flex items-center gap-2">
          <select 
            className="bg-bg-canvas border border-border rounded text-[13px] text-text-primary outline-none focus:ring-1 focus:ring-accent py-1 px-2 h-7"
            value={runId || ''}
            onChange={(e) => setRunId(e.target.value)}
          >
            {runs?.map(r => {
              const dt = new Date(r.init_time);
              const fmt = `${dt.toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' })} 00Z · ${r.source_model}`;
              return <option key={r.run_id} value={r.run_id}>{fmt}</option>;
            })}
            {!runs && <option>Loading runs...</option>}
          </select>
          <div className="px-2 py-0.5 rounded bg-bg-raised border border-border text-text-muted text-[11px] uppercase tracking-wider font-semibold">
            Demo (synthetic)
          </div>
        </div>
      </div>

      {/* Centre: Computed Alert Pill */}
      <div className="flex items-center justify-center flex-1">
        {highRiskRegions.length > 0 && (
          <button 
            onClick={handleAlertClick}
            className="flex items-center gap-2 px-3 py-1 bg-status-red/10 border border-status-red text-status-red hover:bg-status-red hover:text-white transition-colors"
          >
            <span className="text-[12px] font-mono uppercase tracking-wider font-bold">
              [!] {highRiskRegions.length} region{highRiskRegions.length > 1 ? 's' : ''} ≥ 80% Risk
            </span>
          </button>
        )}
      </div>

      {/* Right: Status, Timestamps, Actions */}
      <div className="flex items-center gap-5 flex-1 justify-end">
        
        {/* Status Dot with simulated latency */}
        <div className="flex items-center gap-2" title="API Status">
          <span className="text-[11px] text-text-muted uppercase font-mono tracking-wider">34ms</span>
          <StatusDot status={health?.status === 'ok' ? 'ok' : 'warn'} />
        </div>

        {/* Timestamps */}
        <div className="flex flex-col text-right font-mono text-[11px] leading-tight">
          <div className="text-text-primary">
            VALID {validTime.toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })} UTC
          </div>
          <div className="text-text-muted">
            LOCAL {time.toLocaleString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' })} IST
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-2 border-l border-border pl-4 ml-1">
          <button className="p-1.5 text-text-muted hover:text-text-primary transition-colors rounded hover:bg-bg-raised">
            <Download size={16} />
          </button>
          <button className="p-1.5 text-text-muted hover:text-text-primary transition-colors rounded hover:bg-bg-raised">
            <HelpCircle size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
