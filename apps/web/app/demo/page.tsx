import Link from "next/link";

export default function DemoPage() {
  return (
    <main>
      <header className="page-header">
        <h1>サービスデモ</h1>
        <p className="muted">学習進捗・ポートフォリオ・応募管理がつながる操作フローを体験できます。</p>
      </header>
      <section>
        <h2>デモで確認できる内容</h2>
        <ul>
          <li>学習計画から成果物作成までの学習導線</li>
          <li>成果物証跡と評価履歴を用いた候補者確認</li>
          <li>応募/提案の進行ステージ管理</li>
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
