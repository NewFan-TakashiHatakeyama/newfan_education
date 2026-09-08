"use client";

import { use, useCallback, useEffect, useState } from "react";

import type { VentureLedgerEntry, VentureLedgerSummary } from "@newfan/contracts";

import {
  deleteVentureLedgerEntry,
  fetchVentureLedger,
  saveVentureLedgerEntry
} from "@/lib/api";

import { Section } from "@/app/components/ui/Section";
import { Drawer } from "@/app/components/ui/Drawer";
import { SkeletonRow } from "@/app/components/ui/Skeleton";
import { EmptyState } from "@/app/components/ui/EmptyState";

import { VentureNav } from "../../../VentureNav";
import { useVentureRole } from "../../../useVentureRole";
import styles from "../../../ventures.module.css";

/** 点検値が「揃っている」側かどうか。原本の語をそのまま見て判定する。 */
function isSettled(verdict: string): boolean {
  return /記録あり|整合|充足|一致|確認済|継続|記法OK|標準依存|記録済/.test(verdict);
}

const ENTRY_STATUS = ["未着手", "確認中", "対応中", "完了", "対象外"];

export default function VentureLedgerPage({
  params
}: {
  params: Promise<{ ventureId: string; ledgerKey: string }>;
}) {
  const { ventureId, ledgerKey } = use(params);
  const [data, setData] = useState<VentureLedgerSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [detail, setDetail] = useState<VentureLedgerEntry | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [newRowKey, setNewRowKey] = useState("");
  const { canEdit } = useVentureRole();

  const refresh = useCallback(() => {
    fetchVentureLedger(ventureId, ledgerKey)
      .then(setData)
      .catch((err: unknown) => {
        // 空の結果を入れないと、読み込み中の骨組みが出たまま止まる。
        setData({ ledger: null, items: [] });
        setError(err instanceof Error ? err.message : "台帳を取得できませんでした。");
      });
  }, [ventureId, ledgerKey]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const openDetail = (entry: VentureLedgerEntry) => {
    setDetail(entry);
    setDraft({ ...entry.values });
  };

  const saveEntry = async (entry: VentureLedgerEntry, values: Record<string, string>) => {
    setSaving(true);
    setError(null);
    try {
      await saveVentureLedgerEntry(ventureId, ledgerKey, { id: entry.id, values });
      refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "保存できませんでした。");
    } finally {
      setSaving(false);
    }
  };

  const save = async () => {
    if (!detail) return;
    const target = detail;
    setDetail(null);
    await saveEntry(target, draft);
  };

  const ledger = data?.ledger ?? null;
  const items = data?.items ?? [];
  // 一覧に出す列。定義列は先頭2つ、入力列は先頭3つに絞って横幅を抑える。
  const previewMaster = (ledger?.masterColumns ?? []).slice(1, 3);
  const previewInput = (ledger?.inputColumns ?? []).slice(0, 3);
  // 原本の点検列。最後の1つ（総合点検）を一覧に出す。
  const checkColumns = ledger?.checkColumns ?? [];
  const checkColumn = checkColumns.length > 0 ? checkColumns[checkColumns.length - 1] : "";

  return (
    <>
      <VentureNav ventureId={ventureId} />

      <Section
        title={ledger?.name ?? "台帳"}
        meta={ledger ? `${ledger.summary}（原本: ${ledger.sourceSheet}）` : undefined}
        theme="company"
        actions={
          ledger && !ledger.seeded && canEdit ? (
            <div className={styles.toolbar} style={{ margin: 0 }}>
              <label className={styles.field}>
                行のID
                <input
                  value={newRowKey}
                  onChange={(event) => setNewRowKey(event.target.value)}
                  placeholder={`例: ${ledger.idColumn}-001`}
                />
              </label>
              <button
                type="button"
                className="primary-button"
                disabled={saving}
                onClick={async () => {
                  setSaving(true);
                  setError(null);
                  try {
                    await saveVentureLedgerEntry(ventureId, ledgerKey, {
                      rowKey: newRowKey || undefined,
                      values: {}
                    });
                    setNewRowKey("");
                    refresh();
                  } catch (err: unknown) {
                    setError(err instanceof Error ? err.message : "行を追加できませんでした。");
                  } finally {
                    setSaving(false);
                  }
                }}
              >
                行を追加
              </button>
            </div>
          ) : null
        }
      >
        {error ? <p className={styles.error}>{error}</p> : null}

        {ledger && ledger.notes.length > 0 ? (
          <div className={styles.note}>
            {ledger.notes.map((note, index) => (
              <div key={index}>{note}</div>
            ))}
          </div>
        ) : null}

        {data === null ? (
          <SkeletonRow />
        ) : items.length === 0 ? (
          <EmptyState
            title="行がありません"
            message={
              ledger?.seeded
                ? "この台帳は点検行を持ちますが、案件に展開されていません。"
                : "「行を追加」から起票してください。"
            }
          />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>{ledger?.idColumn ?? "ID"}</th>
                  {previewMaster.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                  <th>状態</th>
                  {checkColumn ? <th>{checkColumn}</th> : null}
                  {previewInput.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                  <th>更新</th>
                </tr>
              </thead>
              <tbody>
                {items.map((entry) => (
                  <tr key={entry.id}>
                    <td className={styles.taskId}>
                      <button
                        type="button"
                        className={styles.rowButton}
                        onClick={() => openDetail(entry)}
                      >
                        {entry.rowKey}
                      </button>
                    </td>
                    {previewMaster.map((column) => (
                      <td key={column} className={styles.wrapText}>
                        {entry.master[column] ?? "—"}
                      </td>
                    ))}
                    <td>
                      <span className={`${styles.pill} ${styles.pillNeutral}`}>{entry.status}</span>
                    </td>
                    {checkColumn ? (
                      <td className={styles.wrapText}>
                        {entry.derived[checkColumn] ? (
                          <span
                            className={`${styles.pill} ${
                              isSettled(entry.derived[checkColumn])
                                ? styles.pillDone
                                : styles.pillProgress
                            }`}
                          >
                            {entry.derived[checkColumn]}
                          </span>
                        ) : (
                          <span className={styles.muted}>—</span>
                        )}
                      </td>
                    ) : null}
                    {previewInput.map((column) => (
                      <td key={column} className={styles.wrapText}>
                        {entry.values[column] || <span className={styles.muted}>未入力</span>}
                      </td>
                    ))}
                    <td className={styles.muted}>
                      {entry.updatedByName || (entry.values && Object.keys(entry.values).length ? "—" : "")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Drawer
        open={detail !== null}
        title={detail ? `${ledger?.name ?? ""} ${detail.rowKey}` : ""}
        onClose={async () => {
          // 書きかけを黙って捨てない。閉じる前に保存する。
          const pending = detail;
          setDetail(null);
          if (pending && canEdit && JSON.stringify(pending.values) !== JSON.stringify(draft)) {
            await saveEntry(pending, draft);
          }
        }}
      >
        {detail && ledger ? (
          <div>
            {ledger.masterColumns.length > 0 ? (
              <dl className={styles.detailList}>
                {ledger.masterColumns.map((column) => (
                  <div key={column} style={{ display: "contents" }}>
                    <dt>{column}</dt>
                    <dd>{detail.master[column] || "—"}</dd>
                  </div>
                ))}
              </dl>
            ) : null}

            {Object.keys(detail.derived).length > 0 ? (
              <dl className={styles.detailList}>
                {Object.entries(detail.derived).map(([column, value]) => (
                  <div key={column} style={{ display: "contents" }}>
                    <dt>{column}</dt>
                    <dd>{value || "—"}</dd>
                  </div>
                ))}
              </dl>
            ) : null}

            <label className={styles.field}>
              状態
              <select
                value={detail.status}
                disabled={saving || !canEdit}
                onChange={async (event) => {
                  setSaving(true);
                  try {
                    await saveVentureLedgerEntry(ventureId, ledgerKey, {
                      id: detail.id,
                      status: event.target.value
                    });
                    refresh();
                    setDetail({ ...detail, status: event.target.value });
                  } catch (err: unknown) {
                    setError(err instanceof Error ? err.message : "保存できませんでした。");
                  } finally {
                    setSaving(false);
                  }
                }}
              >
                {ENTRY_STATUS.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            {ledger.inputColumns.map((column) => {
              // 原本の入力規則がある列は、自由記述ではなく候補・日付・数値で入力させる。
              const rule = ledger.columnRules[column];
              const value = draft[column] ?? "";
              const onChange = (next: string) =>
                setDraft((current) => ({ ...current, [column]: next }));
              return (
                <label key={column} className={styles.field}>
                  {column}
                  {rule?.type === "select" && rule.options.length > 0 ? (
                    <select
                      value={value}
                      disabled={saving || !canEdit}
                      onChange={(event) => onChange(event.target.value)}
                    >
                      <option value="">未入力</option>
                      {rule.options.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  ) : rule?.type === "date" ? (
                    <input
                      type="date"
                      value={value}
                      disabled={saving || !canEdit}
                      onChange={(event) => onChange(event.target.value)}
                    />
                  ) : rule?.type === "number" ? (
                    <input
                      type="number"
                      value={value}
                      min={rule.min ?? undefined}
                      disabled={saving || !canEdit}
                      onChange={(event) => onChange(event.target.value)}
                    />
                  ) : (
                    <textarea
                      value={value}
                      disabled={saving || !canEdit}
                      onChange={(event) => onChange(event.target.value)}
                    />
                  )}
                </label>
              );
            })}

            <div className={styles.actionRow}>
              {canEdit ? (
                <button type="button" className="primary-button" disabled={saving} onClick={save}>
                  {saving ? "保存中…" : "保存する"}
                </button>
              ) : (
                <span className={styles.muted}>台帳の記入は事業責任者・PdM・編集担当が行います。</span>
              )}
              {canEdit && !detail.isMasterRow ? (
                <button
                  type="button"
                  className="ghost-button"
                  disabled={saving}
                  onClick={async () => {
                    setSaving(true);
                    try {
                      await deleteVentureLedgerEntry(ventureId, ledgerKey, detail.id);
                      setDetail(null);
                      refresh();
                    } catch (err: unknown) {
                      setError(err instanceof Error ? err.message : "削除できませんでした。");
                    } finally {
                      setSaving(false);
                    }
                  }}
                >
                  この行を削除
                </button>
              ) : (
                <span className={styles.muted}>
                  点検行はマスタ由来のため削除できません。対象外にする場合は状態で記録します。
                </span>
              )}
            </div>
          </div>
        ) : null}
      </Drawer>
    </>
  );
}
