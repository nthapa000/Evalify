// Skeleton.jsx — paper-toned placeholders shown while data loads (no layout jump).

function Pulse({ className = "" }) {
  return <div className={`animate-pulse bg-paper-200 rounded-sm ${className}`} />;
}

// Card-shaped placeholder for dashboards
export function SkeletonCard() {
  return (
    <div className="bg-paper-50 border border-paper-300 rounded-sm p-5 space-y-3">
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

// One table row placeholder (3 columns)
export function SkeletonRow() {
  return (
    <tr>
      <td className="px-5 py-3"><Pulse className="h-4 w-32" /></td>
      <td className="px-5 py-3"><Pulse className="h-4 w-24" /></td>
      <td className="px-5 py-3"><Pulse className="h-4 w-16" /></td>
    </tr>
  );
}

export default Pulse;
