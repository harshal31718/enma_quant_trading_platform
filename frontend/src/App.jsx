import { useEffect, useState } from "react";
import PriceChart from "./components/PriceChart";

export default function App() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch("/api/data/historical?symbol=BTC/USDT&timeframe=15m&limit=200")
      .then((res) => res.json())
      .then((json) => {
        const candles = json.candles.map((c) => ({
          time: Math.floor(new Date(c.timestamp).getTime() / 1000),
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }));
        setData(candles);
      })
      .catch(console.error);
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>ENMA Dashboard</h1>
      {data.length > 0 ? <PriceChart data={data} /> : <p>Loading…</p>}
    </div>
  );
}
