// PageWrapper.jsx — page shell: top bar, contents index on the left, and the page itself on paper with
// the exam-booklet red margin rule. Every logged-in page renders inside it.

import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function PageWrapper({ children }) {
  return (
    <div className="flex flex-col h-screen bg-paper-100">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        {/* Scrollable content, written to the right of the margin rule */}
        <main className="flex-1 overflow-y-auto margin-rule">
          <div className="pl-14 pr-8 py-8 max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
