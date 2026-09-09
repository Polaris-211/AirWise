import { useEffect, useState } from "react";

function formatNow(date: Date) {
  return date.toLocaleString();
}

export default function App() {
  const [now, setNow] = useState(() => new Date());
  const [backendStatus, setBackendStatus] = useState("Checking...");

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => {
        if (!res.ok) throw new Error("bad status");
        return res.json();
      })
      .then(() => setBackendStatus("Connected"))
      .catch(() => setBackendStatus("Disconnected"));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <div className="mx-auto max-w-xl px-6 py-16">
        <h1 className="text-4xl font-bold">AirWise</h1>
        <p className="mt-2 text-lg text-slate-500">
          Intelligent Flight Price Monitor
        </p>
        <p className="mt-4 text-sm text-slate-400">{formatNow(now)}</p>

        <div className="mt-8 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-green-800">
          ● Backend Status: {backendStatus}
        </div>
      </div>
    </div>
  );
}
