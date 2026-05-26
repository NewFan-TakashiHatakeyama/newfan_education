import Link from "next/link";

export default function GoalCreateRoutePage() {
  return (
    <main>
      <h1>目標設定画面</h1>
      <section>
        <p className="muted">
          目標設定フォームは学習者ホーム下部に実装済みです。仕様上のRoute例に合わせてこの入口を用意しています。
        </p>
        <Link href="/home">学習者ホームの目標設定フォームへ移動</Link>
      </section>
    </main>
  );
}
