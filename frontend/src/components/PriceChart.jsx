import { useEffect, useRef } from "react";
import { createChart, CandlestickSeries } from "lightweight-charts";

export default function PriceChart({ data }) {
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartRef.current) return;

    const chart = createChart(chartRef.current, {
      width: chartRef.current.offsetWidth,
      height: 420,
      layout: {
        background: { color: "#ffffff" },
        textColor: "#000000",
      },
    });

    const series = chart.addSeries(CandlestickSeries);
    series.setData(data);

    return () => chart.remove();
  }, [data]);

  return (
    <div
      ref={chartRef}
      style={{ width: "100%", height: "420px", border: "1px solid #ddd" }}
    />
  );
}
