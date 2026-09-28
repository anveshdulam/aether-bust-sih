import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';
import {
  ForecastRunSummary,
  ConfidenceMapResponse,
  BustProbabilityRequest,
  BustProbabilityResponse,
  AttributionResponse,
  HealthResponse,
  LeadTime,
  VarCode
} from './types';

export const useRuns = () => {
  return useQuery({
    queryKey: ['runs'],
    queryFn: async () => {
      const res = await apiClient.get<{ items: ForecastRunSummary[] }>('/forecast-runs');
      return res.data.items;
    }
  });
};

export const useConfidenceMap = (runId: string | null, leadTime: LeadTime) => {
  return useQuery({
    queryKey: ['confidence-map', runId, leadTime],
    queryFn: async () => {
      const res = await apiClient.get<ConfidenceMapResponse>(`/confidence/${runId}`, {
        params: { lead_time: leadTime }
      });
      return res.data;
    },
    enabled: !!runId
  });
};

export const useBustProbability = (request: BustProbabilityRequest | null) => {
  return useQuery({
    queryKey: ['bust-probability', request],
    queryFn: async () => {
      const res = await apiClient.post<BustProbabilityResponse>('/bust-probability', request);
      return res.data;
    },
    enabled: !!request && !!request.run_id
  });
};

export const useAttribution = (runId: string | null, variable: VarCode, leadTime: LeadTime, lat: number, lon: number, enabled: boolean) => {
  return useQuery({
    queryKey: ['attribution', runId, variable, leadTime, lat, lon],
    queryFn: async () => {
      const res = await apiClient.get<AttributionResponse>('/attribution', {
        params: { run_id: runId, variable, lead_time: leadTime, lat, lon }
      });
      return res.data;
    },
    enabled: !!runId && enabled
  });
};

export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await apiClient.get<HealthResponse>('/health');
      return res.data;
    },
    refetchInterval: 30000
  });
};

export const useBustDetections = (runId: string | null) => {
  return useQuery({
    queryKey: ['bust-detections', runId],
    queryFn: async () => {
      // It returns Page[BustDetection], so we extract items
      const res = await apiClient.get<{ items: any[] }>('/bust-detections', { params: { run_id: runId } });
      return res.data.items;
    },
    enabled: !!runId
  });
};

export const useBaselines = (variable?: string) => {
  return useQuery({
    queryKey: ['baselines', variable],
    queryFn: async () => {
      const res = await apiClient.get<{ items: any[] }>('/baselines', { params: { variable } });
      return res.data.items;
    }
  });
};

export const useTelemetry = () => {
  return useQuery({
    queryKey: ['telemetry'],
    queryFn: async () => {
      const res = await apiClient.get<{ items: any[] }>('/telemetry', { params: { limit: 10 } });
      return res.data.items;
    },
    refetchInterval: 15000 // Poll every 15s per TRD
  });
};
