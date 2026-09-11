import Link from "next/link";

export default function BusinessSignUpPage() {
  return (
    <main>
      <header className="page-header">
        <h1>法人利用を始める</h1>
        <p className="muted">AI研修から、企業課題を解決するシステム開発へ。担当者アカウントを作成して始めましょう。</p>
      </header>
      <section>
        <h2>利用開始までの流れ</h2>
        <ol>
          <li>担当者情報を登録</li>
          <li>企業プロフィールと業務課題を設定</li>
          <li>学習・スキル確認と開発プロジェクトを開始</li>
        </ol>
        <div className="inline-actions">
          <Link href="/auth/sign-up?role=recruiter">担当者アカウントを作成</Link>
          <Link href="/#examples">活用イメージを見る</Link>
          <Link href="/">LPへ戻る</Link>
        </div>
      </section>
    </main>
  );
}
