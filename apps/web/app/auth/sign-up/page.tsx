"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSyncExternalStore, useState } from "react";

import { getRoleHomePath, setDemoAuthSession } from "@/lib/auth";
import { signUpDemoUser } from "@/lib/api";

export default function SignUpPage() {
  const router = useRouter();
  const [userId, setUserId] = useState("");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const linkedInvitation = useSyncExternalStore(
    (notify) => { window.addEventListener("hashchange", notify); return () => window.removeEventListener("hashchange", notify); },
    () => new URLSearchParams(window.location.hash.slice(1)).get("invitation") ?? "",
    () => ""
  );
  const [manualInvitation, setInvitationToken] = useState<string | null>(null);
  const invitationToken = manualInvitation ?? linkedInvitation;
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
        invitationToken,
        password,
      });
      setDemoAuthSession(session);
      router.replace(getRoleHomePath(session.role));
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
        <p className="muted">管理者から届いた参加リンクで登録します。招待の有効期間は7日間です。</p>
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
        <label htmlFor="sign-up-invitation">招待トークン</label>
        <input id="sign-up-invitation" value={invitationToken} onChange={event => setInvitationToken(event.target.value)} />
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
            disabled={submitting || !invitationToken || !userId.trim() || !email.trim() || !displayName.trim() || !password}
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
