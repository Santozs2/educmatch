import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode }

const base =
  'font-bold rounded-xl min-h-[56px] px-8 flex items-center justify-center transition-all duration-200 w-full'

export function ButtonPrimary({ children, className = '', type = 'button', ...resto }: Props) {
  return (
    <button
      type={type}
      className={`bg-red-600 hover:bg-red-700 active:bg-red-900 active:scale-[0.98] disabled:bg-ink-300 disabled:active:scale-100 disabled:opacity-70 text-white shadow-sm hover:shadow-md ${base} ${className}`}
      {...resto}
    >
      {children}
    </button>
  )
}

export function ButtonSecondary({ children, className = '', type = 'button', ...resto }: Props) {
  return (
    <button
      type={type}
      className={`bg-white border-2 border-red-600 text-red-600 hover:bg-red-50 active:bg-red-100 active:scale-[0.98] shadow-sm hover:shadow-md ${base} ${className}`}
      {...resto}
    >
      {children}
    </button>
  )
}

export function ButtonGhost({ children, className = '', type = 'button', ...resto }: Props) {
  return (
    <button
      type={type}
      className={`bg-transparent text-red-600 hover:bg-red-50 active:bg-red-100 active:scale-[0.98] ${base} ${className}`}
      {...resto}
    >
      {children}
    </button>
  )
}