import { useRef, useState } from 'react'
import { ApiError, uploadReport } from '../api/client'

const ACCEPTED = '.pdf,.png,.jpg,.jpeg'

export function UploadForm({ onUploaded }: { onUploaded: (reportId: string) => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    setBusy(true)
    setError(null)
    try {
      const report = await uploadReport(file)
      onUploaded(report.id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not upload the file')
    } finally {
      setBusy(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <div className="upload-form">
      <label className="button button-primary">
        {busy ? 'Uploading…' : 'Upload report'}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          onChange={handleChange}
          disabled={busy}
          hidden
        />
      </label>
      {error && <p className="error-text">{error}</p>}
    </div>
  )
}
