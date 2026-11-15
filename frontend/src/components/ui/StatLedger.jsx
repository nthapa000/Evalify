// StatLedger.jsx — summary numbers in one ruled row (like the totals line of a mark register).

export default function StatLedger({ items }) {
  return (
    <dl className="grid border-y border-paper-900 divide-x divide-paper-300"
        style={{ gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))` }}>
      {items.map((it) => (
        <div key={it.label} className="px-4 py-3">
          <dt className="kicker">{it.label}</dt>
          <dd className="font-mono text-2xl text-paper-900 mt-1">{it.value}</dd>
        </div>
      ))}
    </dl>
  );
}
