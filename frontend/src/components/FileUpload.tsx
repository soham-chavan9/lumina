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
    <section className="desk-panel p-5 md:p-6">
      <p className="desk-kicker">Corpus</p>
      <h2 className="mt-1 text-[1.45rem] text-[var(--ink)]">File policies</h2>
      <p className="mt-1 text-sm leading-relaxed text-[var(--muted)]">
        File Notice of Privacy Practices, breach/IRP procedures, BAA playbooks, and workforce
        sanctions policies. Start with <code className="text-[var(--teal)]">HIPAA_Sample_Compliance.pdf</code>.
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
        className={`mt-4 flex cursor-pointer flex-col items-center justify-center rounded-[16px] border border-dashed px-4 py-11 transition ${
          dragOver
            ? 'border-[var(--teal)] bg-[var(--teal-soft)]'
            : 'border-[var(--line)] bg-[rgba(20,24,31,0.02)]'
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
          <Loader2 className="mb-2 animate-spin text-[var(--teal)]" size={22} />
        ) : (
          <Upload className="mb-2 text-[var(--teal)]" size={22} />
        )}
        <span className="text-sm font-semibold text-[var(--ink)]">
          {uploading ? 'Filing documents…' : 'Drop PDFs or browse'}
        </span>
        <span className="mt-1 text-xs text-[var(--faint)]">PDF · max 15MB each · text-extractable</span>
      </label>
    </section>
  )
}
