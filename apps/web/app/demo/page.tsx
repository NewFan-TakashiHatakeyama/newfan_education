import Link from "next/link";

export default function DemoPage() {
  return (
    <main>
      <header className="page-header">
        <h1>サービスデモ</h1>
        <p className="muted">
          業務課題の登録からAIテーマ化、成果物レビュー、PoC候補選定までの操作フローを体験できます。
        </p>
      </header>
      <section>
        <h2>デモで確認できる内容</h2>
        <ul>
          <li>12週間カリキュラムと育成演習の学習導線</li>
          <li>問い合わせ回答支援AIなど、業務課題を題材にした成果物の作成・レビュー</li>
          <li>AIテーマ適合度の評価と、部門向けのPoC候補整理</li>
        </ul>
        <div className="inline-actions">
          <Link href="/auth/sign-in">体験アカウントでサインイン</Link>
          <Link href="/business/sign-up">法人登録へ進む</Link>
          <Link href="/">LPへ戻る</Link>
        </div>
      </section>
    </main>
  );
}
