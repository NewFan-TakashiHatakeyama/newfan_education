"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { setDemoAuthSession } from "@/lib/auth";
import { signUpDemoUser } from "@/lib/api";

export default function SignUpPage() {
  const router = useRouter();
  const [userId, setUserId] = useState("");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"learner" | "recruiter" | "admin" | "content_editor">("learner");
  const [tenantId, setTenantId] = useState("company-demo");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      const session = await signUpDemoUser({
        userId: userId.trim(),
        email: email.trim(),
        displayName: displayName.trim(),
        role,
        password,
        tenantId
      });
      setDemoAuthSession(session);
      router.push("/onboarding");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "登録に失敗しました");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main>
      <header className="page-header">
        <h1>サインアップ</h1>
        <p className="muted">必要事項を入力してアカウントを作成します。</p>
      </header>
      {error ? <p className="error">{error}</p> : null}
      <section>
        <label htmlFor="sign-up-user-id">ユーザーID</label>
        <input
          id="sign-up-user-id"
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
          placeholder="new-user"
        />
        <label htmlFor="sign-up-email">メールアドレス</label>
        <input
          id="sign-up-email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="new-user@example.com"
        />
        <label htmlFor="sign-up-display-name">表示名</label>
        <input
          id="sign-up-display-name"
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder="New User"
        />
        <label htmlFor="sign-up-role">ロール</label>
        <select
          id="sign-up-role"
          value={role}
          onChange={(event) => setRole(event.target.value as "learner" | "recruiter" | "admin" | "content_editor")}
        >
          <option value="learner">learner</option>
          <option value="recruiter">recruiter</option>
          <option value="admin">admin</option>
          <option value="content_editor">content_editor</option>
        </select>
        <label htmlFor="sign-up-tenant-id">Tenant ID</label>
        <input
          id="sign-up-tenant-id"
          value={tenantId}
          onChange={(event) => setTenantId(event.target.value)}
        />
        <label htmlFor="sign-up-password">パスワード</label>
        <input
          id="sign-up-password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <div className="inline-actions">
          <button
            type="button"
            onClick={onSubmit}
            disabled={submitting || !userId.trim() || !email.trim() || !displayName.trim() || !password}
          >
            登録して開始
          </button>
          <Link href="/auth/sign-in">サインインへ</Link>
          <Link href="/">サービス紹介へ</Link>
        </div>
      </section>
    </main>
  );
}
