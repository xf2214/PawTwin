import { useEffect, useRef, useState, type InputHTMLAttributes } from 'react'

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'value' | 'defaultValue' | 'onChange'> & {
  storedValue: string
  displayValue: string
}

// Pristine defaults follow the language; an owner's draft stays verbatim.
export function LocalizedInput({ storedValue, displayValue, ...props }: Props) {
  const [draft, setDraft] = useState<{ original: string; value: string } | null>(null)
  const input = useRef<HTMLInputElement>(null)
  useEffect(() => {
    const form = input.current?.form
    const reset = () => setDraft(null)
    form?.addEventListener('reset', reset)
    return () => form?.removeEventListener('reset', reset)
  }, [])
  const edited = draft !== null
  return <input {...props} ref={input} value={edited ? draft.value : displayValue}
    data-preserve-raw={edited ? undefined : 'true'}
    onChange={event => setDraft({ original: storedValue, value: event.target.value })} />
}

export function storedInputValue(form: HTMLFormElement, name: string, storedValue: string): string {
  const input = form.elements.namedItem(name)
  return input instanceof HTMLInputElement && input.dataset.preserveRaw === 'true'
    ? storedValue : String(new FormData(form).get(name) ?? '').trim()
}
