'use client'

import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { Upload, Loader2 } from 'lucide-react'
import { getErrorMessage, uploadPdfs } from '../lib/api'

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
    const toastId = toast.loading('Indexing into the policy corpus…')
    try {
      const { results } = await uploadPdfs(files)
      const ok = results.filter((r) =>
        r.status.toLowerCase().includes('embedded successfully')
      ).length
      if (ok > 0) {
        toast.success(`${ok} polic${ok === 1 ? 'y' : 'ies'} filed`, { id: toastId })
        onUploadComplete()
      } else {
        toast.error(results[0]?.status || 'Upload failed', { id: toastId })
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'Upload failed'), { id: toastId })
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <section className="desk-panel p-6 md:p-7">
      <p className="desk-kicker">Corpus</p>
      <h2 className="section-title mt-1 text-[1.65rem]">File policies</h2>
      <p className="mt-2 text-[15px] leading-relaxed text-[var(--muted)]">
        Drop Notice of Privacy Practices, breach procedures, BAA playbooks, and sanctions
        policies.
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
        className={`mt-5 flex cursor-pointer flex-col items-center justify-center rounded-[18px] border border-dashed px-4 py-12 transition-all duration-200 ${
          dragOver
            ? 'border-[var(--accent)] bg-[var(--accent-soft)] scale-[1.01]'
            : 'border-[var(--line-strong)] bg-[rgba(0,0,0,0.02)]'
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
          <Loader2 className="mb-3 animate-spin text-[var(--accent)]" size={24} />
        ) : (
          <Upload className="mb-3 text-[var(--accent)]" size={24} strokeWidth={1.75} />
        )}
        <span className="text-[15px] font-semibold tracking-[-0.01em] text-[var(--ink)]">
          {uploading ? 'Filing documents…' : 'Drop PDFs or browse'}
        </span>
        <span className="mt-1.5 text-[13px] text-[var(--faint)]">
          PDF · max 15MB each · text-extractable
        </span>
      </label>
    </section>
  )
}
