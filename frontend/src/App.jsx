// App.jsx — root router.
// Phase 0: shows a placeholder landing page.
// Phase 1 will replace this with proper route guards and page components.

import { Routes, Route } from "react-router-dom";

function Placeholder() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-indigo-600 mb-2">Evalify</h1>
        <p className="text-gray-500">Phase 0 — Infrastructure ready. UI coming in Phase 1.</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="*" element={<Placeholder />} />
    </Routes>
  );
}
