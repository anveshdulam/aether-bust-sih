import { scaleLinear } from 'd3-scale';
import { ColorStop } from '../theme/colormaps';

export function createColorScale(stops: ColorStop[], domainMax: number = 1) {
  const domain = stops.map(s => s.stop * domainMax);
  
  const rScale = scaleLinear<number>().domain(domain).range(stops.map(s => s.rgba[0])).clamp(true);
  const gScale = scaleLinear<number>().domain(domain).range(stops.map(s => s.rgba[1])).clamp(true);
  const bScale = scaleLinear<number>().domain(domain).range(stops.map(s => s.rgba[2])).clamp(true);
  const aScale = scaleLinear<number>().domain(domain).range(stops.map(s => s.rgba[3])).clamp(true);

  return (value: number): [number, number, number, number] => {
    return [
      Math.round(rScale(value)),
      Math.round(gScale(value)),
      Math.round(bScale(value)),
      Math.round(aScale(value))
    ];
  };
}

export function createCssColorScale(stops: ColorStop[], domainMax: number = 1) {
  const rgbaScale = createColorScale(stops, domainMax);
  return (value: number) => {
    const [r, g, b, a] = rgbaScale(value);
    return `rgba(${r}, ${g}, ${b}, ${a / 255})`;
  };
}
