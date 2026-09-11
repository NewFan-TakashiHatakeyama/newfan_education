"use client";
import { useEffect, useState } from "react";

export function Feedback({ message, error = false }: { message: string | null; error?: boolean }) {
  const [dismissed, setDismissed] = useState<string | null>(null);
  useEffect(() => {
    if (!message || error) return;
    const timer = window.setTimeout(() => setDismissed(message), 5000);
    return () => window.clearTimeout(timer);
  }, [message, error]);
  if (!message || (!error && dismissed === message)) return null;
  return <div className={error ? "inline-error" : "save-notice"} role={error ? "alert" : "status"}>{message}</div>;
}
