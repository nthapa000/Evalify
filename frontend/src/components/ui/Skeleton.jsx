// Skeleton.jsx — animated placeholder shown while data is loading.
// Use skeletons instead of spinners to avoid layout shifts.

function Pulse({ className = "" }) {
  return <div className={`animate-pulse bg-gray-200 rounded-lg ${className}`} />;
}

// Single-card skeleton matching paper cards on dashboards
export function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-3">
      <Pulse className="h-4 w-2/3" />
      <Pulse className="h-3 w-1/3" />
      <Pulse className="h-3 w-1/2" />
      <div className="flex gap-2 pt-2">
        <Pulse className="h-7 w-20" />
        <Pulse className="h-7 w-20" />
      </div>
    </div>
  );
}

// One table row skeleton (3 columns)
export function SkeletonRow() {
  return (
    <tr>
      <td className="px-6 py-4"><Pulse className="h-4 w-32" /></td>
      <td className="px-6 py-4"><Pulse className="h-4 w-24" /></td>
      <td className="px-6 py-4"><Pulse className="h-4 w-16" /></td>
    </tr>
  );
}

export default Pulse;
