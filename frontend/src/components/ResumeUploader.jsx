import React, { useState, useRef } from 'react';
import ApiService from '../utils/api';
import { UploadCloud, CheckCircle, AlertCircle, Loader2, FileUp } from 'lucide-react';

export default function ResumeUploader({ onUploadComplete }) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState(null); // { success: X, failed: Y }
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const processFiles = async (files) => {
    if (files.length === 0) return;
    
    setUploading(true);
    setError('');
    setStatus(null);

    // Verify all are PDFs
    const pdfFiles = Array.from(files).filter(f => f.type === "application/pdf" || f.name.toLowerCase().endsWith('.pdf'));
    if (pdfFiles.length === 0) {
      setError("Please upload only PDF resumes");
      setUploading(false);
      return;
    }

    try {
      const response = await ApiService.uploadResumes(pdfFiles);
      setStatus({
        success: response.total_success,
        failed: response.total_failed,
        failures: response.failures || []
      });
      if (response.total_success > 0) {
        onUploadComplete();
      }
    } catch (err) {
      setError(err.message || "Failed to upload and parse resumes");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFiles(e.target.files);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current.click();
  };

  return (
    <div className="space-y-4 text-left">
      <h2 className="text-xl font-bold flex items-center gap-2 font-sans">
        <FileUp className="w-5 h-5 text-brand-500" />
        Resume Processing
      </h2>

      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`glass-panel border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition relative ${
          dragActive
            ? 'border-brand-500 bg-brand-500/5'
            : 'border-slate-800 hover:border-slate-700 bg-slate-900/10'
        } ${uploading ? 'opacity-70 pointer-events-none' : ''}`}
        onClick={onButtonClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf"
          onChange={handleChange}
          className="hidden"
        />

        {uploading ? (
          <div className="py-6 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-10 h-10 text-brand-500 animate-spin" />
            <p className="text-sm font-semibold text-slate-200">
              Extracting Text & Generating Vector Embeddings...
            </p>
            <p className="text-2xs text-slate-400">
              Analyzing entities via spaCy and structuring with Gemini
            </p>
          </div>
        ) : (
          <div className="py-6 flex flex-col items-center justify-center gap-2">
            <UploadCloud className="w-10 h-10 text-slate-400 group-hover:text-brand-500 transition mb-2" />
            <p className="text-sm font-semibold text-slate-200">
              Drag & drop candidate PDF resumes here
            </p>
            <p className="text-2xs text-slate-500">
              or click to browse local files (Multiple PDF upload supported)
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/20 text-red-200 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {status && (
        <div className="glass-panel p-4 rounded-xl space-y-2 border-l-2 border-green-500 animate-fade-in text-xs">
          <div className="flex items-center gap-2 text-slate-200 font-semibold">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span>Processing Summary</span>
          </div>
          <p className="text-slate-400 mt-1">
            Successfully indexed <strong className="text-green-400">{status.success}</strong> candidates into Supabase & ChromaDB.
            {status.failed > 0 && (
              <>
                {' '}Failed to process <strong className="text-red-400">{status.failed}</strong> files.
              </>
            )}
          </p>
          {status.failures.length > 0 && (
            <div className="bg-slate-950/50 p-2 rounded max-h-24 overflow-y-auto text-2xs font-mono text-red-400 space-y-1">
              {status.failures.map((fail, idx) => (
                <div key={idx}>• {fail.filename}: {fail.error}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
