import { forwardRef, HTMLAttributes } from 'react'
import { clsx } from 'clsx'

interface ToasterProps extends HTMLAttributes<HTMLDivElement> {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center'
}

const Toaster = forwardRef<HTMLDivElement, ToasterProps>(
  ({ className, position = 'top-right', ...props }, ref) => {
    const positions = {
      'top-right': 'top-0 right-0',
      'top-left': 'top-0 left-0',
      'bottom-right': 'bottom-0 right-0',
      'bottom-left': 'bottom-0 left-0',
      'top-center': 'top-0 left-1/2 -translate-x-1/2',
      'bottom-center': 'bottom-0 left-1/2 -translate-x-1/2'
    }

    return (
      <div
        ref={ref}
        className={clsx(
          'fixed z-50 p-4 pointer-events-none',
          positions[position],
          className
        )}
        {...props}
      />
    )
  }
)

Toaster.displayName = 'Toaster'

interface ToastProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'destructive' | 'success'
}

const Toast = forwardRef<HTMLDivElement, ToastProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const variants = {
      default: 'bg-white border border-gray-200 text-gray-900',
      destructive: 'bg-red-50 border border-red-200 text-red-800',
      success: 'bg-green-50 border border-green-200 text-green-800'
    }

    return (
      <div
        ref={ref}
        className={clsx(
          'pointer-events-auto rounded-lg p-4 shadow-lg mb-2 max-w-sm',
          variants[variant],
          className
        )}
        {...props}
      />
    )
  }
)

Toast.displayName = 'Toast'

export { Toaster, Toast }