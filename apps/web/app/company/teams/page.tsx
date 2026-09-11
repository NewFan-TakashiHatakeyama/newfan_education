"use client";

import { FormEvent, useEffect, useState } from "react";

import { Modal } from "@/app/components/ui/Drawer";
import { Feedback } from "@/app/components/ui/Feedback";
import { useVentureRole } from "@/app/ventures/useVentureRole";
import type { Team } from "@newfan/contracts";
import { createTeam, getTeams, inviteUser, inviteUsersByCsv } from "@/lib/api";

export default function CompanyTeamsPage() {
  const [panel, setPanel] = useState<"team" | "invite" | "csv" | null>(null);
  const [busy, setBusy] = useState(false);
  const { role, canManage } = useVentureRole();
  const [inviteLinks, setInviteLinks] = useState<{ email: string; url: string }[]>([]);
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
    if (busy) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await createTeam({ name, description });
      setName("");
      setDescription("");
      refresh();
      setMessage("チームを作成しました。"); setPanel(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "チーム作成に失敗しました");
    } finally { setBusy(false); }
  }

  async function submitInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await inviteUser({ email: inviteEmail, role: inviteRole });
      setInviteLinks([{ email: result.email, url: `${window.location.origin}/auth/sign-up#invitation=${encodeURIComponent(result.token)}` }]);
      setInviteEmail(""); setPanel(null);
      setMessage(`招待を発行しました: ${result.email}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "招待に失敗しました");
    } finally { setBusy(false); }
  }

  async function submitCsvImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await inviteUsersByCsv({ csvContent, defaultRole: "learner" });
      setInviteLinks(result.created.map(item => ({ email: item.email, url: `${window.location.origin}/auth/sign-up#invitation=${encodeURIComponent(item.token)}` })));
      setPanel(null); setCsvContent("");
      setMessage(`参加リンク発行: ${result.created.length}件作成 / ${result.skipped.length}件スキップ`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSVインポートに失敗しました");
    } finally { setBusy(false); }
  }

  return (
    <main>
      <div className="page-header">
        <h1>チーム管理</h1>

      </div>
      <div className="page-actions">
        {canManage && <button className="primary-button" onClick={() => { setError(null); setPanel("team"); }}>チームを作成</button>}
        {role === "admin" && <><button onClick={() => { setError(null); setPanel("invite"); }}>ユーザーを招待</button><button onClick={() => { setError(null); setPanel("csv"); }}>一括招待</button></>}
      </div>
      <Feedback message={error} error /><Feedback message={message} />
      {inviteLinks.length > 0 && <section><h2>参加リンク（7日間・1回限り）</h2><p>メールは自動送信されません。各本人に対応するリンクを渡してください。</p>
        {inviteLinks.map(item => <div key={item.email}><label>{item.email}<input readOnly value={item.url} onFocus={e => e.target.select()} /></label><button type="button" onClick={async () => { try { await navigator.clipboard.writeText(item.url); setMessage("参加リンクをコピーしました。"); } catch { setError("コピーできませんでした。リンクを選択してコピーしてください。"); } }}>リンクをコピー</button></div>)}</section>}


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

      <Modal open={panel === "team"} title="チーム作成" onClose={() => { setPanel(null); setName(""); setDescription(""); }} busy={busy} dirty={!!name || !!description}>
        <Feedback message={error} error />
        <form onSubmit={submitTeam}>
          <label htmlFor="team-name">チーム名</label>
          <input id="team-name" value={name} onChange={(event) => setName(event.target.value)} required />
          <label htmlFor="team-description">説明</label>
          <input
            id="team-description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <button type="submit" disabled={busy}>作成</button>
        </form>
      </Modal>

      <Modal open={panel === "invite"} title="ユーザー招待" onClose={() => { setPanel(null); setInviteEmail(""); setInviteRole("learner"); }} busy={busy} dirty={!!inviteEmail || inviteRole !== "learner"}>
        <Feedback message={error} error />
        <form onSubmit={submitInvite}>
          <label htmlFor="invite-email">メールアドレス</label>
          <input
            type="email"
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
            <option value="learner">受講者</option>
            <option value="mentor">メンター</option>
            <option value="recruiter">企業担当者</option>
            <option value="content_editor">教材編集者</option>
            <option value="admin">管理者</option>
          </select>
          <button type="submit" disabled={busy}>参加リンクを発行</button>
        </form>
      </Modal>

      <Modal open={panel === "csv"} title="CSV一括招待" onClose={() => { setPanel(null); setCsvContent(""); }} busy={busy} dirty={!!csvContent}>
        <Feedback message={error} error />
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
          <button type="submit" disabled={busy}>参加リンクを一括発行</button>
        </form>
      </Modal>
    </main>
  );
}
