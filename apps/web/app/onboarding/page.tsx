"use client";

import Link from "next/link";
import { getCurrentDemoAuthSession } from "@/lib/api";

export default function OnboardingPage() {
  const session = getCurrentDemoAuthSession();

  return (
    <main>
      <header className="page-header">
        <h1>オンボーディング</h1>
        <p className="muted">
          ロールと利用コンテキストを確認し、同意設定・目標設定・学習開始へ案内します。
        </p>
      </header>

      <section>
        <h2>初期コンテキスト確認</h2>
        <p>{`ユーザー: ${session?.userId ?? "loading..."} / ロール: ${session?.role ?? "loading..."}`}</p>
        <p className="muted">
          ロールが期待と異なる場合は、サインイン画面で切り替えてから続行してください。
        </p>
        <div className="inline-actions">
          <Link href="/auth/sign-in">サインインを開く</Link>
          <Link href="/auth/sign-up">新規登録を開く</Link>
        </div>
      </section>

      <section>
        <h2>同意ガイダンス</h2>
        <ul>
          <li>学習データ・証跡データの利用目的を確認して同意してください。</li>
          <li>同意はいつでも変更可能で、変更履歴は設定画面で確認できます。</li>
          <li>企業向けレポートに使う証跡品質を高めるため、演習提出時の記述を具体化してください。</li>
        </ul>
      </section>

      <section>
        <h2>次のアクション</h2>
        <div className="inline-actions">
          <Link href="/goals/new">目標を設定する</Link>
          <Link href="/settings/consents">同意設定を確認する</Link>
          <Link href="/learner/learn">受講者ホームへ進む</Link>
        </div>
      </section>
    </main>
  );
}
