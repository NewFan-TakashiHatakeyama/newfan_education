"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { getRoleHomePath, setDemoAuthSession } from "@/lib/auth";
import { signInDemoUser } from "@/lib/api";

const DEMO_ACCOUNTS = [
  {
    roleLabel: "学習者",
    email: "learner@example.com",
    password: "Learner123!",
    hint: "学習ホーム・成果物へ"
  },
  {
    roleLabel: "企業担当",
    email: "recruiter@example.com",
    password: "Recruiter123!",
    hint: "企業ダッシュボードへ"
  },
  {
    roleLabel: "管理者",
    email: "admin@example.com",
    password: "Admin123!",
    hint: "管理画面へ"
  }
] as const;

const SHOW_DEMO_ACCOUNTS = process.env.NODE_ENV !== "production";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState(SHOW_DEMO_ACCOUNTS ? "learner@example.com" : "");
  const [password, setPassword] = useState(SHOW_DEMO_ACCOUNTS ? "Learner123!" : "");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      const session = await signInDemoUser({ email: email.trim(), password });
      setDemoAuthSession(session);
      router.replace(getRoleHomePath(session.role));
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "サインインに失敗しました");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main>
      <header className="page-header">
        <h1>サインイン</h1>
        <p className="muted">
          学習者・企業担当・管理者など、登録済みアカウントでサインインします。
        </p>
      </header>
      {error ? <p className="error">{error}</p> : null}
      {SHOW_DEMO_ACCOUNTS && <section aria-label="デモアカウント">
        <p className="muted" style={{ marginTop: 0 }}>
          まずは学習者で操作感を確認できます。企業向け画面は企業担当でサインインしてください。
        </p>
        <div className="inline-actions" style={{ flexWrap: "wrap", gap: "0.5rem" }}>
          {DEMO_ACCOUNTS.map((account) => (
            <button
              key={account.email}
              type="button"
              className="ghost-button"
              onClick={() => {
                setEmail(account.email);
                setPassword(account.password);
                setError(null);
              }}
            >
              {account.roleLabel}（{account.hint}）
            </button>
          ))}
        </div>
      </section>}
      <section>
        <label htmlFor="sign-in-email">メールアドレス</label>
        <input
          id="sign-in-email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="learner@example.com"
        />
        <label htmlFor="sign-in-password">パスワード</label>
        <input
          id="sign-in-password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <div className="inline-actions">
          <button type="button" onClick={onSubmit} disabled={submitting || !email.trim() || !password}>
            サインイン
          </button>
          <Link href="/auth/sign-up">新規登録へ</Link>
          <Link href="/">サービス紹介へ</Link>
        </div>
      </section>
    </main>
  );
}
