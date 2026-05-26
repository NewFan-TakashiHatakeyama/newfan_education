"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  createConsent,
  createGoal,
  generateRoadmap,
  getDashboard,
  getMyConsents,
  getNotifications,
  listCurriculumVersions,
  postProgressEvent
} from "@/lib/api";
import { buildNotificationCenterLink } from "@/lib/notificationLinks";
import { EmptyState } from "@/app/components/product/EmptyState";
import { RoadmapTimeline } from "@/app/components/product/RoadmapTimeline";
import { SkillGapCard } from "@/app/components/product/SkillGapCard";
import { VisibilityBadge } from "@/app/components/product/VisibilityBadge";
import type {
  ConsentRecord,
  CurriculumVersion,
  DashboardSummary,
  Goal,
  NotificationItem,
  Roadmap
} from "@newfan/contracts";

const EMPTY_HOME_UNREAD_COUNTS = {
  learning: 0,
  career: 0,
  dm: 0,
  admin: 0
};
const EMPTY_HOME_FIRST_UNREAD_IDS = {
  learning: null as string | null,
  career: null as string | null,
  dm: null as string | null,
  admin: null as string | null
};

export default function LearnerHomePage() {
  const [consentType, setConsentType] =
    useState<"career_profile" | "talent_search">("career_profile");
  const [consents, setConsents] = useState<ConsentRecord[]>([]);
  const [goal, setGoal] = useState<Goal | null>(null);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [curriculum, setCurriculum] = useState<CurriculumVersion[]>([]);
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationsLoading, setNotificationsLoading] = useState(true);
  const [unreadByCategory, setUnreadByCategory] = useState(EMPTY_HOME_UNREAD_COUNTS);
  const [firstUnreadIdByCategory, setFirstUnreadIdByCategory] = useState(EMPTY_HOME_FIRST_UNREAD_IDS);
  const [goalTitle, setGoalTitle] = useState("Pythonバックエンド案件に参画したい");
  const [goalType, setGoalType] = useState("転職");
  const [targetRole, setTargetRole] = useState("Backend Engineer");
  const [hoursPerWeek, setHoursPerWeek] = useState(8);
  const [currentConcern, setCurrentConcern] = useState("API設計の実務経験が不足している");
  const [error, setError] = useState<string | null>(null);
  const importantNotifications = notifications.filter((item) => item.isImportant);
  const regularNotifications = notifications.filter((item) => !item.isImportant);
  const orderedNotifications = [...importantNotifications, ...regularNotifications];

  async function run<T>(fn: () => Promise<T>, apply: (data: T) => void) {
    try {
      setError(null);
      const result = await fn();
      apply(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    }
  }

  async function loadDashboard() {
    setDashboardLoading(true);
    await run(getDashboard, setDashboard);
    setDashboardLoading(false);
  }

  useEffect(() => {
    let active = true;
    getNotifications()
      .then((summary) => {
        if (!active) {
          return;
        }
        setNotifications(summary.items.slice(0, 3));
        const nextUnreadCounts = { ...EMPTY_HOME_UNREAD_COUNTS };
        const nextFirstUnreadIds = { ...EMPTY_HOME_FIRST_UNREAD_IDS };
        for (const item of summary.items) {
          if (item.readAt !== null) {
            continue;
          }
          nextUnreadCounts[item.category] += 1;
          if (nextFirstUnreadIds[item.category] === null) {
            nextFirstUnreadIds[item.category] = item.id;
          }
        }
        setUnreadByCategory(nextUnreadCounts);
        setFirstUnreadIdByCategory(nextFirstUnreadIds);
      })
      .catch(() => {
        if (active) {
          setNotifications([]);
          setUnreadByCategory(EMPTY_HOME_UNREAD_COUNTS);
          setFirstUnreadIdByCategory(EMPTY_HOME_FIRST_UNREAD_IDS);
        }
      })
      .finally(() => {
        if (active) {
          setNotificationsLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <main>
      <header className="page-header">
        <div className="page-title-row">
          <h1>学習者ホーム</h1>
          <VisibilityBadge mode="limited" />
        </div>
        <p className="muted">
          今日やること、ロードマップ、進捗、スキル差分、教材更新通知を一画面で確認します。
        </p>
      </header>
      {error && <p className="error">{error}</p>}

      <section>
        <h2>今日の次アクションカード</h2>
        <p className="muted">
          次の教材: {roadmap?.items[0]?.title ?? "ロードマップを生成すると表示されます"}
        </p>
        <p className="muted">
          推定所要時間: {roadmap?.items[0]?.estimatedMinutes ?? 30}分 / 理由: 目標との差分が大きい基礎領域
        </p>
        <div className="inline-actions">
          <button
            type="button"
            disabled={!roadmap?.items[0]}
            onClick={() =>
              run(
                () =>
                  postProgressEvent({
                    roadmapId: roadmap?.id,
                    roadmapItemId: roadmap?.items[0].id,
                    eventType: "lesson_completed"
                  }),
                () => undefined
              )
            }
          >
            学習を再開
          </button>
          <Link href="/learn">教材一覧を見る</Link>
          <button type="button" onClick={loadDashboard}>
            進捗を更新
          </button>
        </div>
      </section>

      <div className="grid">
        <section>
          <h2>進捗カード</h2>
          {dashboardLoading ? (
            <div>
              <div className="skeleton" />
              <div className="skeleton" />
              <div className="skeleton" />
            </div>
          ) : null}
          <div className="kpi">
            <div>
              <strong>完了率</strong>
              <p>{Math.round((dashboard?.completionRate ?? 0) * 100)}%</p>
            </div>
            <div>
              <strong>完了教材</strong>
              <p>
                {dashboard?.completedItems ?? 0}/{dashboard?.totalItems ?? 0}
              </p>
            </div>
            <div>
              <strong>連続学習日数</strong>
              <p>3日</p>
            </div>
          </div>
        </section>

        <section>
          <h2>スキル差分カード</h2>
          <ul className="card-list">
            <SkillGapCard skill="API設計" current={2} target={3} evidenceCount={4} />
            <SkillGapCard skill="認証設計" current={1} target={3} evidenceCount={2} />
            <SkillGapCard skill="Python基礎" current={3} target={3} evidenceCount={7} />
          </ul>
          <Link href="/skills">スキル差分を詳しく見る</Link>
        </section>
      </div>

      <section>
        <h2>ロードマップタイムライン</h2>
        {!roadmap && (
          <EmptyState
            title="ロードマップなし"
            message="目標を設定して、あなた専用のロードマップを作成しましょう"
            action={<button onClick={() => document.getElementById("goalTitle")?.focus()}>目標設定へ</button>}
          />
        )}
        <RoadmapTimeline roadmap={roadmap} />
        {roadmap && <Link href={`/roadmaps/${roadmap.id}`}>ロードマップ詳細へ</Link>}
      </section>

      <div className="split">
        <section>
          <h2>最近の成果物</h2>
          <ul className="card-list">
            <li>
              FastAPI Todo API（評価: A） <VisibilityBadge mode="public" />
            </li>
            <li>
              Python基礎課題（評価: B+） <VisibilityBadge mode="limited" />
            </li>
          </ul>
          <Link href="/learner/evidence">成果物一覧へ</Link>
        </section>

        <section>
          <h2>通知・教材更新</h2>
          <div className="inline-actions">
            <Link
              href={buildNotificationCenterLink({
                category: "learning",
                unreadOnly: true,
                selectedId: firstUnreadIdByCategory.learning ?? undefined
              })}
              className="status-pill"
            >
              {`学習 未読 ${unreadByCategory.learning}`}
            </Link>
            <Link
              href={buildNotificationCenterLink({
                category: "career",
                unreadOnly: true,
                selectedId: firstUnreadIdByCategory.career ?? undefined
              })}
              className="status-pill"
            >
              {`キャリア 未読 ${unreadByCategory.career}`}
            </Link>
            <Link
              href={buildNotificationCenterLink({
                category: "dm",
                unreadOnly: true,
                selectedId: firstUnreadIdByCategory.dm ?? undefined
              })}
              className="status-pill"
            >
              {`DM 未読 ${unreadByCategory.dm}`}
            </Link>
            <Link
              href={buildNotificationCenterLink({
                category: "admin",
                unreadOnly: true,
                selectedId: firstUnreadIdByCategory.admin ?? undefined
              })}
              className="status-pill"
            >
              {`運営 未読 ${unreadByCategory.admin}`}
            </Link>
          </div>
          {notificationsLoading ? (
            <>
              <div className="skeleton" />
              <div className="skeleton" />
              <div className="skeleton" />
            </>
          ) : (
            <>
              <ul className="card-list">
                {orderedNotifications.map((item) => (
                  <li key={item.id}>
                    <strong>{item.title}</strong>
                    {item.isImportant ? (
                      <div className="inline-actions">
                        <span className="status-pill pill-warm">重要</span>
                      </div>
                    ) : null}
                    <p className="muted">{item.body}</p>
                    <Link
                      href={buildNotificationCenterLink({
                        category: item.category,
                        selectedId: item.id
                      })}
                    >
                      この通知を通知センターで開く
                    </Link>
                  </li>
                ))}
              </ul>
              {notifications.length === 0 ? (
                <EmptyState
                  title="通知なし"
                  message="新しい通知はありません。学習や応募を進めるとここに表示されます。"
                />
              ) : null}
            </>
          )}
          <div className="inline-actions">
            <Link
              href={
                notifications[0]
                  ? buildNotificationCenterLink({
                      category: notifications[0].category,
                      selectedId: notifications[0].id
                    })
                  : "/notifications"
              }
            >
              通知センターを開く
            </Link>
            <Link href="/settings/consents">同意管理を開く</Link>
          </div>
        </section>
      </div>

      <section>
        <h2>目標設定画面</h2>
        <div className="split">
          <div>
            <label htmlFor="goalTitle">目標タイトル</label>
            <input
              id="goalTitle"
              value={goalTitle}
              onChange={(e) => setGoalTitle(e.target.value)}
            />
            <label htmlFor="goalType">目標タイプ</label>
            <select id="goalType" value={goalType} onChange={(e) => setGoalType(e.target.value)}>
              <option value="転職">転職</option>
              <option value="副業">副業</option>
              <option value="社内スキルアップ">社内スキルアップ</option>
              <option value="学習のみ">学習のみ</option>
            </select>
            <label htmlFor="targetRole">目標職種</label>
            <input
              id="targetRole"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
            />
            <label htmlFor="hoursPerWeek">週学習時間（1〜40）</label>
            <input
              id="hoursPerWeek"
              type="number"
              min={1}
              max={40}
              value={hoursPerWeek}
              onChange={(e) => setHoursPerWeek(Number(e.target.value))}
            />
            <label htmlFor="concern">現在の悩み</label>
            <input
              id="concern"
              value={currentConcern}
              onChange={(e) => setCurrentConcern(e.target.value)}
            />
          </div>
          <div className="right-panel">
            <h3>生成前確認</h3>
            <p>目標: {goalTitle}</p>
            <p>目標タイプ: {goalType}</p>
            <p>目標職種: {targetRole}</p>
            <p>学習時間: 週{hoursPerWeek}時間</p>
            <p>現在地: {currentConcern}</p>
            <p className="muted">この内容でロードマップを生成しますか？</p>
          </div>
        </div>
        <div className="inline-actions">
          <button
            type="button"
            onClick={() =>
              run(
                () =>
                  createGoal({
                    title: goalTitle,
                    targetRole,
                    availableHoursPerWeek: hoursPerWeek
                  }),
                setGoal
              )
            }
          >
            下書き保存
          </button>
          {goal && (
            <>
              <button
                type="button"
                onClick={() =>
                  run(
                    () => generateRoadmap({ goalId: goal.id, preferredDifficulty: 2 }),
                    setRoadmap
                  )
                }
              >
                ロードマップを生成
              </button>
            </>
          )}
        </div>
        {goal && <p className="muted">保存済み目標ID: {goal.id}</p>}
      </section>

      <section>
        <h2>キャリア公開同意（クイック操作）</h2>
        <div className="split">
          <div>
            <label htmlFor="consentType">同意種別</label>
            <select
              id="consentType"
              value={consentType}
              onChange={(e) =>
                setConsentType(e.target.value as "career_profile" | "talent_search")
              }
            >
              <option value="career_profile">企業にプロフィールを表示</option>
              <option value="talent_search">案件/求人推薦に学習データを利用</option>
            </select>
            <div className="inline-actions">
              <button
                type="button"
                onClick={() =>
                  run(
                    () => createConsent({ consentType, granted: true }),
                    (created) => setConsents((prev) => [created, ...prev])
                  )
                }
              >
                同意を保存
              </button>
              <button type="button" onClick={() => run(getMyConsents, setConsents)}>
                同意履歴を再取得
              </button>
              <Link href="/settings/consents">同意管理画面へ</Link>
            </div>
          </div>
          <div className="right-panel">
            <p className="muted">同意時には公開範囲・利用目的・取り消し可能性を明示します。</p>
            <ul>
              <li>対象データ: プロフィール、スキル、成果物</li>
              <li>提供範囲: 企業/営業の許可済みユーザー</li>
              <li>取り消し: いつでも設定画面から可能</li>
            </ul>
          </div>
        </div>
      </section>

      <section>
        <h2>教材版管理（高優先その3）</h2>
        <div className="inline-actions">
          <button type="button" onClick={() => run(listCurriculumVersions, setCurriculum)}>
            教材一覧を取得
          </button>
          <Link href="/learn">教材画面へ</Link>
        </div>
        <ul className="card-list">
          {curriculum.map((version) => (
            <li key={version.id}>
              <strong>{version.title}</strong>
              <p className="muted">
                {version.curriculumSlug} / v{version.version}
              </p>
            </li>
          ))}
        </ul>
        {curriculum.length === 0 && (
          <EmptyState
            title="教材なし"
            message="ロードマップと連動した教材がまだ読み込まれていません"
            action={<button onClick={() => run(listCurriculumVersions, setCurriculum)}>再読み込み</button>}
          />
        )}
      </section>

      <section>
        <h2>内部デバッグ情報</h2>
        <details>
          <summary>APIレスポンスを表示</summary>
          <pre>{JSON.stringify({ goal, roadmap, dashboard, consents, curriculum }, null, 2)}</pre>
        </details>
      </section>
    </main>
  );
}
