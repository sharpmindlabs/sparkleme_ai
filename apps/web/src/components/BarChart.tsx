// Lightweight SVG bar chart — no external chart library (per spec, simple is fine).

export function BarChart({
  data,
  labels,
  color = "#0d9488",
  suffix = "",
}: {
  data: number[];
  labels: string[];
  color?: string;
  suffix?: string;
}) {
  const max = Math.max(...data, 1) * 1.15;
  const w = 560;
  const h = 150;
  const bw = w / data.length;
  return (
    <svg viewBox={`0 0 ${w} ${h + 24}`} className="w-full" role="img" aria-label="bar chart">
      {data.map((d, i) => {
        const bh = (d / max) * h;
        const x = i * bw + 10;
        return (
          <g key={i}>
            <rect x={x} y={h - bh} width={bw - 20} height={bh} rx={5} fill={color} />
            <text x={i * bw + bw / 2} y={h - bh - 6} fontSize={11} textAnchor="middle" fill="#475569">
              {d}
              {suffix}
            </text>
            <text x={i * bw + bw / 2} y={h + 16} fontSize={10.5} textAnchor="middle" fill="#94a3b8">
              {labels[i]}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
