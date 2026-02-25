import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";

type PlotlyChartProps = {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
};

export function PlotlyChart({ data, layout, config }: PlotlyChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    Plotly.react(container, data, layout, {
      responsive: true,
      displaylogo: false,
      ...config,
    });

    return () => {
      Plotly.purge(container);
    };
  }, [config, data, layout]);

  return <div className="plotly-chart" ref={containerRef} />;
}
