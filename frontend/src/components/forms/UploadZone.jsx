// UploadZone.jsx — drag-and-drop image upload area.
// Used on the answer-key step (teacher) and the submission page (student).

import { useState, useRef } from "react";

export default function UploadZone({ onFileSelect, accept = "image/*", label = "Upload Image", hint = "PNG, JPG up to 10 MB" }) {
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState(null);
  const [fileName, setFileName] = useState("");
  const inputRef = useRef();

  const handleFile = (file) => {
    if (!file) return;
    setFileName(file.name);
    // Create a local object URL for image preview
    if (file.type.startsWith("image/")) {
      setPreview(URL.createObjectURL(file));
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
        ${dragging ? "border-indigo-400 bg-indigo-50" : "border-gray-300 hover:border-indigo-300 hover:bg-gray-50"}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />

      {preview ? (
        // Show image thumbnail once a file is selected
        <div className="space-y-2">
          <img src={preview} alt="preview" className="mx-auto max-h-48 rounded-lg object-contain" />
          <p className="text-sm text-gray-500 truncate">{fileName}</p>
          <p className="text-xs text-indigo-600 font-medium">Click to replace</p>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="mx-auto w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center text-2xl">📄</div>
          <p className="text-sm font-medium text-gray-700">{label}</p>
          <p className="text-xs text-gray-400">Drag & drop or click to browse</p>
          <p className="text-xs text-gray-400">{hint}</p>
        </div>
      )}
    </div>
  );
}
