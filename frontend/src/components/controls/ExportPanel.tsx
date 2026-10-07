import { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';

const API_BASE = 'http://localhost:8000/api/v1';

export const ExportPanel = () => {
  const { runId, variable, leadTime } = useAppStore();
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleDownload = async (layer: 'p_bust' | 'expected_error' | 'confidence', format: 'geojson' | 'geotiff' | 'netcdf') => {
    if (!runId) return;
    
    // Construct export URL
    const url = `${API_BASE}/export?run_id=${runId}&variable=${variable}&layer=${layer}&lead_time=${leadTime}&format=${format}`;
    
    try {
      setDownloading(`${layer}-${format}`);
      const response = await fetch(url);
      
      if (!response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `aether_bust_${layer}_day${leadTime}.${format === 'geojson' ? 'json' : format === 'geotiff' ? 'tif' : 'nc'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      a.remove();
    } catch (err) {
      console.error('Download failed:', err);
      alert('Failed to download the requested format.');
    } finally {
      setDownloading(null);
    }
  };

  if (!runId) return null;

  return (
    <div className="mt-8 flex flex-col gap-2">
      <div className="flex justify-between items-center pb-2 border-b border-border mb-2">
        <span className="text-xs font-mono text-text-muted uppercase tracking-widest">Data Export</span>
        <span className="text-[10px] bg-accent/10 text-accent px-1.5 py-0.5 border border-accent/20 rounded">Day {leadTime}</span>
      </div>
      
      <div className="flex flex-col gap-2 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-text-primary text-xs">Bust Probability</span>
          <div className="flex gap-1">
            <button 
              onClick={() => handleDownload('p_bust', 'geojson')}
              disabled={downloading === 'p_bust-geojson'}
              className="px-2 py-1 bg-bg-raised rounded border border-border text-xs text-text-muted hover:border-accent hover:text-accent disabled:opacity-50 transition-colors"
            >
              GeoJSON
            </button>
            <button 
              onClick={() => handleDownload('p_bust', 'netcdf')}
              disabled={downloading === 'p_bust-netcdf'}
              className="px-2 py-1 bg-bg-raised rounded border border-border text-xs text-text-muted hover:border-accent hover:text-accent disabled:opacity-50 transition-colors"
            >
              NetCDF
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-text-primary text-xs">Expected Error</span>
          <div className="flex gap-1">
            <button 
              onClick={() => handleDownload('expected_error', 'geotiff')}
              disabled={downloading === 'expected_error-geotiff'}
              className="px-2 py-1 bg-bg-raised rounded border border-border text-xs text-text-muted hover:border-accent hover:text-accent disabled:opacity-50 transition-colors"
            >
              GeoTIFF
            </button>
            <button 
              onClick={() => handleDownload('expected_error', 'netcdf')}
              disabled={downloading === 'expected_error-netcdf'}
              className="px-2 py-1 bg-bg-raised rounded border border-border text-xs text-text-muted hover:border-accent hover:text-accent disabled:opacity-50 transition-colors"
            >
              NetCDF
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
