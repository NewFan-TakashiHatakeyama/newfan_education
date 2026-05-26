"use client";

import { FormEvent, useEffect, useState } from "react";

import type { Team } from "@newfan/contracts";
import { createTeam, getTeams, inviteUser, inviteUsersByCsv } from "@/lib/api";

export default function CompanyTeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"learner" | "mentor" | "recruiter" | "content_editor" | "admin">("learner");
  const [csvContent, setCsvContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = () => {
    getTeams()
      .then((result) => setTeams(result.items))
      .catch((err) => setError(err instanceof Error ? err.message : "チーム取得に失敗しました"));
  };

  useEffect(() => {
    refresh();
  }, []);

  async function submitTeam(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await createTeam({ name, description });
      setName("");
      setDescription("");
      refresh();
      setMessage("チームを作成しました。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "チーム作成に失敗しました");
    }
  }

  async function submitInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      const result = await inviteUser({ email: inviteEmail, role: inviteRole });
      setInviteEmail("");
      setMessage(`招待を発行しました: ${result.email}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "招待に失敗しました");
    }
  }

  async function submitCsvImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      const result = await inviteUsersByCsv({ csvContent, defaultRole: "learner" });
      setMessage(`CSVインポート完了: ${result.created.length}件作成 / ${result.skipped.length}件スキップ`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSVインポートに失敗しました");
    }
  }

  return (
    <main>
      <div className="page-header">
        <h1>チーム管理</h1>
        <p className="muted">チーム作成、ユーザー招待、CSV一括招待を管理します。</p>
      </div>
      {error ? <p className="error">{error}</p> : null}
      {message ? <p>{message}</p> : null}

      <section>
        <h2>チーム一覧</h2>
        <ul className="card-list">
          {teams.map((team) => (
            <li key={team.id}>
              <strong>{team.name}</strong>
              <p className="muted">{team.description ?? "説明なし"}</p>
            </li>
          ))}
          {teams.length === 0 ? <li>チームがありません。</li> : null}
        </ul>
      </section>

      <section>
        <h2>チーム作成</h2>
        <form onSubmit={submitTeam}>
          <label htmlFor="team-name">チーム名</label>
          <input id="team-name" value={name} onChange={(event) => setName(event.target.value)} required />
          <label htmlFor="team-description">説明</label>
          <input
            id="team-description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <button type="submit">作成</button>
        </form>
      </section>

      <section>
        <h2>ユーザー招待</h2>
        <form onSubmit={submitInvite}>
          <label htmlFor="invite-email">メールアドレス</label>
          <input
            id="invite-email"
            value={inviteEmail}
            onChange={(event) => setInviteEmail(event.target.value)}
            required
          />
          <label htmlFor="invite-role">ロール</label>
          <select
            id="invite-role"
            value={inviteRole}
            onChange={(event) => setInviteRole(event.target.value as typeof inviteRole)}
          >
            <option value="learner">learner</option>
            <option value="mentor">mentor</option>
            <option value="recruiter">recruiter</option>
            <option value="content_editor">content_editor</option>
            <option value="admin">admin</option>
          </select>
          <button type="submit">招待を送る</button>
        </form>
      </section>

      <section>
        <h2>CSV一括招待</h2>
        <form onSubmit={submitCsvImport}>
          <label htmlFor="csv-content">メール一覧（1行1件）</label>
          <textarea
            id="csv-content"
            rows={6}
            value={csvContent}
            onChange={(event) => setCsvContent(event.target.value)}
            placeholder={"user1@example.com\nuser2@example.com"}
            required
          />
          <button type="submit">CSV取り込み</button>
        </form>
      </section>
    </main>
  );
}
