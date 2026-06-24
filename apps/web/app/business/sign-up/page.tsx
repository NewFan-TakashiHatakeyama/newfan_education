import Link from "next/link";

export default function BusinessSignUpPage() {
  return (
    <main>
      <header className="page-header">
        <h1>法人向けサインアップ</h1>
        <p className="muted">社内AI人材育成プログラムの導入・管理を開始できます。</p>
      </header>
      <section>
        <h2>利用開始までの流れ</h2>
        <ol>
          <li>担当者情報を登録</li>
          <li>企業プロフィールと業務課題を設定</li>
          <li>受講者の育成・成果物レビューを開始</li>
        </ol>
        <div className="inline-actions">
          <Link href="/auth/sign-up?role=recruiter">担当者アカウントを作成</Link>
          <Link href="/demo">まずデモを見る</Link>
          <Link href="/">LPへ戻る</Link>
        </div>
      </section>
    </main>
  );
}
