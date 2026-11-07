'use client'

import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { Upload, Loader2 } from 'lucide-react'
import { uploadPdfs } from '../lib/api'

type Props = {
  onUploadComplete: () => void
}

export default function FileUpload({ onUploadComplete }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)

  const processFiles = async (files: FileList | File[] | null) => {
    if (!files || Array.from(files).length === 0) return
    setUploading(true)
    const toastId = toast.loading('Indexing policy PDF…')
    try {
      const { results } = await uploadPdfs(files)
      const ok = results.filter((r) =>
        r.status.toLowerCase().includes('embedded successfully')
      ).length
      if (ok > 0) {
        toast.success(`${ok} file${ok === 1 ? '' : 's'} indexed`, { id: toastId })
        onUploadComplete()
      } else {
        toast.error(results[0]?.status || 'Upload failed', { id: toastId })
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed'
      toast.error(message, { id: toastId })
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <section className="lumina-panel p-5 md:p-6">
      <p className="text-[13px] font-semibold uppercase tracking-[0.08em] text-[var(--lumina-faint)]">
        Ingest
      </p>
      <h2 className="mt-1 text-[22px] font-semibold tracking-tight">Upload policies</h2>
      <p className="mt-1 text-sm text-[var(--lumina-muted)]">
        Drop PDF policies to embed them into Lumina’s private index.
      </p>

      <label
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          void processFiles(e.dataTransfer.files)
        }}
        className={`mt-4 flex cursor-pointer flex-col items-center justify-center rounded-[18px] border border-dashed px-4 py-10 transition ${
          dragOver
            ? 'border-[var(--lumina-blue)] bg-[var(--lumina-blue-soft)]'
            : 'border-[var(--lumina-line)] bg-[rgba(0,0,0,0.015)]'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          multiple
          className="hidden"
          disabled={uploading}
          onChange={(e) => void processFiles(e.target.files)}
        />
        {uploading ? (
          <Loader2 className="mb-2 animate-spin text-[var(--lumina-blue)]" size={22} />
        ) : (
          <Upload className="mb-2 text-[var(--lumina-blue)]" size={22} />
        )}
        <span className="text-sm font-semibold text-[var(--lumina-ink)]">
          {uploading ? 'Embedding…' : 'Click or drag PDFs here'}
        </span>
        <span className="mt-1 text-xs text-[var(--lumina-faint)]">Up to 15MB per file</span>
      </label>
    </section>
  )
}
