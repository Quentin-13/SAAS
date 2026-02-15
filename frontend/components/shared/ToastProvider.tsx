"use client";

import { Toaster } from "react-hot-toast";

export function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          background: "hsl(222.2 84% 4.9%)",
          color: "hsl(210 40% 98%)",
          border: "1px solid hsl(217.2 32.6% 17.5%)",
        },
      }}
    />
  );
}
