// ta/Dashboard.jsx — the TA's review queue: pick a subject, then the "Flagged by AI" or
// "Re-evaluation requests" tab. Each item is one answer sheet; "Review" opens it.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import PageWrapper from "../../components/layout/PageWrapper";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import { SkeletonCard } from "../../components/ui/Skeleton";
import { useTaSubjects, useTaQueue } from "../../hooks/useTa";

const TABS = [
  { key: "flagged", label: "Flagged by AI", count: "flagged" },
  { key: "reevaluation", label: "Re-evaluation requests", count: "reevaluation" },
];

// One answer sheet waiting for the TA
function QueueItem({ item, tab }) {
  return (
    <Card>
      <Card.Body className="flex flex-col md:flex-row md:items-start gap-4">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-800">{item.student_name}</p>
          <p className="text-xs text-gray-500">{item.roll_no} · {item.paper_name} · AI score {item.totalScore} / {item.maxScore}</p>
          {/* Flagged: one reason per question; re-evaluation: the student's remark */}
          {tab === "flagged" ? (
            <ul className="mt-2 space-y-1">
              {item.questions.map((q) => (
                <li key={q.question} className="text-sm text-amber-700">{q.question}: {q.reason}</li>
              ))}
            </ul>
          ) : (
            <blockquote className="mt-2 text-sm text-gray-700 bg-gray-50 border-l-4 border-green-500 px-3 py-2 rounded">
              {item.remark}
            </blockquote>
          )}
        </div>
        <Link to={`/ta/review/${item.submission_id}?tab=${tab}`}>
          <Button size="sm">Review</Button>
        </Link>
      </Card.Body>
    </Card>
  );
}

export default function TaDashboard() {
  const { subjects, loading } = useTaSubjects();
  const [subject, setSubject] = useState("");
  const [tab, setTab] = useState("flagged");
  const { items, loading: loadingItems } = useTaQueue(subject, tab);

  // Start with the first subject once the list arrives
  useEffect(() => { if (!subject && subjects.length) setSubject(subjects[0].subject); }, [subjects, subject]);
  const current = subjects.find((s) => s.subject === subject);

  return (
    <PageWrapper>
      <h1 className="text-2xl font-bold text-gray-800">Answer sheets to review</h1>
      <p className="text-sm text-gray-500 mt-1 mb-6">Your marks are final; the student sees the updated marks and their history.</p>

      {/* Subjects the TA is TA of */}
      <div className="flex flex-wrap gap-2 mb-4">
        {loading ? <SkeletonCard /> : subjects.map((s) => (
          <button key={s.subject} type="button" onClick={() => setSubject(s.subject)}
            className={`px-4 py-2 rounded-lg text-sm font-medium border ${s.subject === subject
              ? "bg-green-600 text-white border-green-600" : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"}`}>
            {s.subject}
            <Badge variant={s.subject === subject ? "neutral" : "warning"} className="ml-2">{s.flagged + s.reevaluation}</Badge>
          </button>
        ))}
        {!loading && subjects.length === 0 && <p className="text-sm text-gray-400">You are not a TA of any subject yet.</p>}
      </div>

      {/* The two tabs */}
      {current && (
        <div role="tablist" className="flex gap-1 border-b border-gray-200 mb-4">
          {TABS.map((t) => (
            <button key={t.key} role="tab" type="button" aria-selected={tab === t.key} onClick={() => setTab(t.key)}
              className={`px-4 py-2 text-sm font-medium -mb-px border-b-2 ${tab === t.key
                ? "border-green-600 text-green-700" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
              {t.label} ({current[t.count]})
            </button>
          ))}
        </div>
      )}

      {/* Items of the selected tab */}
      <div className="space-y-3">
        {loadingItems ? <SkeletonCard /> : items.length === 0 && current
          ? <p className="text-center py-12 text-gray-400">Nothing to review in this tab.</p>
          : items.map((it) => <QueueItem key={it.submission_id} item={it} tab={tab} />)}
      </div>
    </PageWrapper>
  );
}
