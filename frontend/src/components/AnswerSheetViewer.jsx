// AnswerSheetViewer.jsx — every page of a submitted answer sheet (loaded with the login token).
// Used by the TA review screen; students and teachers can use it too (same access rules on the server).

import { useEffect, useState } from "react";
import api from "../services/api";

export default function AnswerSheetViewer({ submissionId }) {
  const [urls, setUrls] = useState([]);
  const [error, setError] = useState("");

  // Page count, then each page as an image blob (the files need the Authorization header)
  useEffect(() => {
    let alive = true;
    const made = [];
    (async () => {
      try {
        const { data } = await api.get(`/submissions/${submissionId}/pages`);
        const out = [];
        for (let i = 0; i < data.count; i++) {
          const res = await api.get(`/submissions/${submissionId}/pages/${i}`, { responseType: "blob" });
          const url = URL.createObjectURL(res.data);
          made.push(url);
          out.push(url);
        }
        if (alive) setUrls(out);
      } catch {
        if (alive) setError("Could not load the answer sheet.");
      }
    })();
    return () => { alive = false; made.forEach((u) => URL.revokeObjectURL?.(u)); };
  }, [submissionId]);

  if (error) return <p className="text-sm text-red-500">{error}</p>;
  if (!urls.length) return <p className="text-sm text-gray-400">Loading answer sheet…</p>;
  return (
    <div className="space-y-3">
      {urls.map((u, i) => (
        <figure key={u} className="border border-gray-200 rounded-lg overflow-hidden bg-white">
          {/* Click a page to open it full size */}
          <a href={u} target="_blank" rel="noreferrer">
            <img src={u} alt={`Answer sheet page ${i + 1}`} className="w-full" />
          </a>
          <figcaption className="text-xs text-gray-400 px-2 py-1">Page {i + 1} of {urls.length}</figcaption>
        </figure>
      ))}
    </div>
  );
}
