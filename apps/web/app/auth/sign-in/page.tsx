"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { getRoleHomePath, setDemoAuthSession } from "@/lib/auth";
import { signInDemoUser } from "@/lib/api";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("Admin123!");
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
        <p className="muted">登録済みアカウントでサインインします。</p>
      </header>
      {error ? <p className="error">{error}</p> : null}
      <section>
        <label htmlFor="sign-in-email">メールアドレス</label>
        <input
          id="sign-in-email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="admin@example.com"
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
