import { scaleLinear } from 'd3-scale';
import { ColorStop } from '../theme/colormaps';

export function createColorScale(stops: ColorStop[], domainMax: number = 1) {
  const domain = stops.map(s => s.stop * domainMax);
  
  // rgba is [r, g, b, a] where a is 0-255
  const colors = stops.map(s => {
    return { r: s.rgba[0], g: s.rgba[1], b: s.rgba[2], opacity: s.rgba[3] / 255 };
  });
  
  const rScale = scaleLinear<number>().domain(domain).range(colors.map(c => c.r)).clamp(true);
  const gScale = scaleLinear<number>().domain(domain).range(colors.map(c => c.g)).clamp(true);
  const bScale = scaleLinear<number>().domain(domain).range(colors.map(c => c.b)).clamp(true);
  const aScale = scaleLinear<number>().domain(domain).range(colors.map(c => c.opacity)).clamp(true);

  return (value: number): [number, number, number, number] => {
    return [
      Math.round(rScale(value)),
      Math.round(gScale(value)),
      Math.round(bScale(value)),
      aScale(value)
    ];
  };
}

export function createCssColorScale(stops: ColorStop[], domainMax: number = 1) {
  const domain = stops.map(s => s.stop * domainMax);
  const range = stops.map(s => `rgba(${s.rgba[0]},${s.rgba[1]},${s.rgba[2]},${s.rgba[3]/255})`);
  
  const colorScale = scaleLinear<string>().domain(domain).range(range).clamp(true);
  
  return (value: number) => {
    return colorScale(value);
  };
}
