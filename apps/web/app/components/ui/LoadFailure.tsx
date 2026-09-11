"use client";
export function LoadFailure({ onRetry }: { onRetry: () => void }) {
  return <div className="inline-error" role="alert"><p>データを取得できませんでした。件数・判定は確認できていません。</p><button type="button" onClick={onRetry}>再試行</button></div>;
}
