// PageWrapper.jsx — full-page shell: Navbar on top, Sidebar on left, content on right.
// Every authenticated page renders inside this wrapper.

import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function PageWrapper({ children }) {
  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        {/* Scrollable main content area */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
