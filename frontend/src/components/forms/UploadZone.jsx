// UploadZone.jsx — drag-and-drop file upload area.
// Supports PDF, PNG, and JPG for student answer-sheet uploads.

import { useState, useRef } from "react";

export default function UploadZone({
  onFileSelect,
  accept = "application/pdf,image/png,image/jpeg",
  label = "Upload Answer Sheet",
  hint = "PDF, PNG, or JPG · Max 10 MB",
}) {
  const [dragging, setDragging]   = useState(false);
  const [fileName, setFileName]   = useState("");
  const [preview, setPreview]     = useState(null);
  const inputRef = useRef();

  const handleFile = (file) => {
    if (!file) return;
    setFileName(file.name);

    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf && file.type.startsWith("image/")) {
      setPreview(URL.createObjectURL(file));
    } else {
      setPreview(null);
    }

    onFileSelect?.(file);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      className={`
        cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-colors
        ${dragging ? "border-green-400 bg-green-50" : "border-gray-300 hover:border-green-300 hover:bg-gray-50"}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />

      {fileName ? (
        <div className="space-y-2">
          {preview ? (
            <img src={preview} alt="preview" className="mx-auto max-h-48 rounded-lg object-contain" />
          ) : (
            /* PDF or non-image file — show icon instead of image preview */
            <div className="mx-auto w-16 h-16 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center text-3xl">
              📄
            </div>
          )}
          <p className="text-sm font-medium text-gray-700 truncate px-4">{fileName}</p>
          <p className="text-xs text-green-600 font-medium">✓ File selected — click to replace</p>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="mx-auto w-12 h-12 rounded-full bg-green-100 flex items-center justify-center text-2xl">📄</div>
          <p className="text-sm font-medium text-gray-700">{label}</p>
          <p className="text-xs text-gray-400">Drag & drop or click to browse</p>
          <p className="text-xs text-gray-400">{hint}</p>
        </div>
      )}
    </div>
  );
}
