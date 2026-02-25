import { ChartDataBundle } from "../lib/types";
import { PlotlyChart } from "./PlotlyChart";

type ChartsPanelProps = {
  marketMode: "bear" | "bull";
  charts: ChartDataBundle;
  isLoading: boolean;
  error: string;
};

export function ChartsPanel({ marketMode, charts, isLoading, error }: ChartsPanelProps) {
  const isBearMode = marketMode === "bear";

  return (
    <section className="panel">
      <h2>Charts</h2>
      {isLoading && <p className="status">Loading charts...</p>}
      {error && <p className="status error">{error}</p>}

      <div className="chart-block">
        <h3>Price vs Share (without time modifier)</h3>
        <PlotlyChart
          data={[
            {
              type: "scatter",
              mode: "lines",
              name: "share",
              x: charts.line_points.map((row) => row.price),
              y: charts.line_points.map((row) => row.base_share_pct),
              line: { color: "#0f766e", width: 2.8 },
              hovertemplate:
                "Price: $%{x:,.0f}<br>share: %{y:.2f}%<extra></extra>",
            },
          ]}
          layout={{
            paper_bgcolor: "#ffffff",
            plot_bgcolor: "#f8fbff",
            margin: { l: 56, r: 20, t: 20, b: 50 },
            xaxis: {
              title: {
                text: isBearMode
                  ? "Expected price path (left high -> right low)"
                  : "Expected price path (left low -> right high)",
              },
              tickprefix: "$",
              tickformat: ",.0f",
              autorange: isBearMode ? "reversed" : true,
            },
            yaxis: {
              title: { text: "Share (%)" },
              range: [0, 100],
            },
            legend: {
              orientation: "h",
              y: 1.13,
              x: 0,
            },
          }}
        />
      </div>

      {charts.heatmap_surface ? (
        <>
          <div className="chart-block">
            <h3>Heatmap</h3>
            <PlotlyChart
              data={[
                {
                  type: "heatmap",
                  x: charts.heatmap_surface.day_offsets,
                  y: charts.heatmap_surface.prices_desc,
                  z: charts.heatmap_surface.z_target_share_pct,
                  colorscale: "Viridis",
                  customdata: charts.heatmap_surface.time_iso,
                  hovertemplate:
                    "Date: %{customdata}<br>Price: $%{y:,.0f}<br>target_share: %{z:.2f}%<extra></extra>",
                },
              ]}
              layout={{
                paper_bgcolor: "#ffffff",
                plot_bgcolor: "#f8fbff",
                margin: { l: 56, r: 20, t: 20, b: 72 },
                xaxis: {
                  title: { text: "Date" },
                  tickvals: charts.heatmap_surface.tick_vals,
                  ticktext: charts.heatmap_surface.tick_text,
                  tickangle: -30,
                  automargin: true,
                },
                yaxis: {
                  title: { text: "Price (USD)" },
                  tickprefix: "$",
                  tickformat: ",.0f",
                },
              }}
            />
          </div>

          <div className="chart-block">
            <h3>3D Surface</h3>
            <PlotlyChart
              data={[
                {
                  type: "surface",
                  x: charts.heatmap_surface.day_offsets,
                  y: charts.heatmap_surface.prices_desc,
                  z: charts.heatmap_surface.z_target_share_pct,
                  colorscale: "Cividis",
                },
              ]}
              layout={{
                paper_bgcolor: "#ffffff",
                margin: { l: 0, r: 0, t: 20, b: 20 },
                scene: {
                  xaxis: {
                    title: { text: "Date" },
                    tickvals: charts.heatmap_surface.tick_vals,
                    ticktext: charts.heatmap_surface.tick_text,
                  },
                  yaxis: {
                    title: { text: "Price (USD)" },
                    tickprefix: "$",
                    tickformat: ",.0f",
                  },
                  zaxis: {
                    title: { text: "Share (%)" },
                  },
                },
              }}
            />
          </div>
        </>
      ) : (
        <p className="status muted">{charts.heatmap_status || "No time segments"}</p>
      )}
    </section>
  );
}
