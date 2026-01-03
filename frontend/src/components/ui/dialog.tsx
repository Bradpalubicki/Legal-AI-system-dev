import { forwardRef, HTMLAttributes } from 'react'
import { Dialog as HeadlessDialog, DialogPanel, DialogTitle as HeadlessDialogTitle, Description } from '@headlessui/react'
import { clsx } from 'clsx'

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}

const Dialog = ({ open, onOpenChange, children }: DialogProps) => {
  return (
    <HeadlessDialog open={open} onClose={() => onOpenChange(false)} className="relative z-50">
      <div className="fixed inset-0 bg-black/25" />
      <div className="fixed inset-0 flex w-screen items-center justify-center p-4">
        {children}
      </div>
    </HeadlessDialog>
  )
}

const DialogContent = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <DialogPanel
    ref={ref}
    className={clsx(
      'relative max-h-[85vh] w-full max-w-lg overflow-auto rounded-lg bg-white p-6 shadow-lg',
      className
    )}
    {...props}
  />
))

DialogContent.displayName = 'DialogContent'

const DialogHeader = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={clsx('flex flex-col space-y-1.5 text-center sm:text-left', className)}
    {...props}
  />
))

DialogHeader.displayName = 'DialogHeader'

const DialogTitle = forwardRef<
  HTMLHeadingElement,
  HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <HeadlessDialogTitle
    ref={ref}
    className={clsx('text-lg font-semibold leading-none tracking-tight', className)}
    {...props}
  />
))

DialogTitle.displayName = 'DialogTitle'

const DialogDescription = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <Description
    ref={ref}
    className={clsx('text-sm text-gray-500', className)}
    {...props}
  />
))

DialogDescription.displayName = 'DialogDescription'

export {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
}