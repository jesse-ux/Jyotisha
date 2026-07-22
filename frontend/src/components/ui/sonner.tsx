"use client"

import { Toaster as Sonner, type ToasterProps } from "sonner"

function Toaster(props: ToasterProps) {
  return (
    <Sonner
      position="bottom-right"
      closeButton={false}
      toastOptions={{
        classNames: {
          toast: "group toast",
          title: "toast-title",
          description: "toast-description",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
