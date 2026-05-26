import Link from "next/link";

export default function AdminHomePage() {
  return (
    <main>
      <div className="page-header">
        <h1>管理ダッシュボード</h1>
        <p className="muted">教材管理やユーザー管理など、運営に必要な機能へ移動できます。</p>
      </div>
      <section>
        <h2>メニュー</h2>
        <ul className="card-list">
          <li><Link href="/admin/curriculum">教材管理へ</Link></li>
          <li><Link href="/admin/users">ユーザー管理へ</Link></li>
          <li><Link href="/admin/companies">企業管理へ</Link></li>
          <li><Link href="/admin/moderation">モデレーションへ</Link></li>
          <li><Link href="/admin/audit-logs">グローバル監査ログへ</Link></li>
          <li><Link href="/admin/task-templates">タスクテンプレート管理へ</Link></li>
        </ul>
      </section>
    </main>
  );
}
