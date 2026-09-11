"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import type { VentureMaster, VentureMasterTask, VentureStandards } from "@newfan/contracts";

import { fetchVentureMaster, fetchVentureMasterTasks, fetchVentureStandards } from "@/lib/api";

import { PageHero } from "@/app/components/ui/PageHero";
import { Section } from "@/app/components/ui/Section";
import { SkeletonRow } from "@/app/components/ui/Skeleton";

import styles from "../ventures.module.css";

/**
 * 工程の標準。案件を作らずに読める参照ページ。
 *
 * 原本 03（Tier別の強度）・04（省略不可の原則と参考工数）・14（ハーネス標準・
 * 標準開発ループ・実行設定・負の試験）・24（調査ソース）・32（評価分類）と、
 * 132の標準タスクを、そのまま読めるようにする。
 */
export default function VentureStandardsPage() {
  const [master, setMaster] = useState<VentureMaster | null>(null);
  const [standards, setStandards] = useState<VentureStandards | null>(null);
  const [tasks, setTasks] = useState<VentureMasterTask[]>([]);
  const [phaseId, setPhaseId] = useState("B0");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchVentureMaster()
      .then(setMaster)
      .catch(() => setMaster(null));
    fetchVentureStandards()
      .then(setStandards)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "工程の標準を取得できませんでした。")
      );
  }, []);

  useEffect(() => {
    fetchVentureMasterTasks(phaseId)
      .then((res) => setTasks(res.items))
      .catch(() => setTasks([]));
  }, [phaseId]);

  return (
    <>
      <PageHero
        eyebrow="案件管理"
        title="工程の標準"
        lead="工程・評価・承認の基準を確認できます。"
        theme="company"
        metrics={[
          { label: "標準タスク", value: master?.taskCount ?? "—", icon: "clipboardCheck" },
          { label: "スキル", value: master?.skillCount ?? "—", icon: "sparkles" },
          { label: "台帳", value: master?.ledgers.length ?? "—", icon: "rocket" }
        ]}
        actions={
          <Link href="/ventures" className="ghost-button">
            案件一覧へ
          </Link>
        }
      />

      {error ? <p className={styles.error}>{error}</p> : null}

      <Section
        title="規模によらず省略できない原則"
        meta="原本04。規模を小さくしても、ここは代替証拠で維持します。"
        theme="company"
      >
        {standards === null ? (
          <SkeletonRow />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>観点</th>
                  <th>適用の考え方</th>
                  <th>具体的な運用</th>
                  <th>留保・禁止する短絡</th>
                </tr>
              </thead>
              <tbody>
                {standards.tailoring.map((item) => (
                  <tr key={item.aspect}>
                    <td>{item.aspect}</td>
                    <td className={styles.wrapText}>{item.approach}</td>
                    <td className={styles.wrapText}>{item.operation}</td>
                    <td className={styles.wrapText}>{item.caution}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Section
        title="Risk Tier 別の評価・承認強度"
        meta="原本03。Tierは社内区分で、法的分類とは分けて扱います。"
        theme="company"
      >
        {master === null ? (
          <SkeletonRow />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Tier</th>
                  <th>典型的な影響・用途</th>
                  <th>評価・承認強度</th>
                  <th>注意</th>
                </tr>
              </thead>
              <tbody>
                {master.riskTiers.map((tier) => (
                  <tr key={tier.tierId}>
                    <td>
                      <span className={styles.taskId}>{tier.tierId}</span> {tier.name}
                    </td>
                    <td className={styles.wrapText}>{tier.impact}</td>
                    <td className={styles.wrapText}>{tier.rigor}</td>
                    <td className={styles.wrapText}>{tier.caution}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Section
        title="規模別の参考構成と参考工数"
        meta="原本04。未較正の目安です。実行予算・人数へそのまま転記しません。"
        theme="company"
      >
        {standards === null ? (
          <SkeletonRow />
        ) : (
          <>
            <div className={styles.tableWrap} style={{ marginBottom: 14 }}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>規模</th>
                    <th>参考構成</th>
                    <th>具体的な運用</th>
                    <th>留保</th>
                  </tr>
                </thead>
                <tbody>
                  {["S", "M", "L"].map((scale) =>
                    (standards.scales[scale] ?? []).map((item, index) => (
                      <tr key={`${scale}-${index}`}>
                        <td>{scale}</td>
                        <td className={styles.wrapText}>{item.approach}</td>
                        <td className={styles.wrapText}>{item.operation}</td>
                        <td className={styles.wrapText}>{item.caution}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>工程</th>
                    <th>S</th>
                    <th>M</th>
                    <th>L</th>
                    <th>単位・範囲</th>
                  </tr>
                </thead>
                <tbody>
                  {standards.effortReference.map((item) => (
                    <tr key={item.phase}>
                      <td>{item.phase}</td>
                      <td>
                        {item.sMin}〜{item.sMax}
                      </td>
                      <td>
                        {item.mMin}〜{item.mMax}
                      </td>
                      <td>
                        {item.lMin}〜{item.lMax}
                      </td>
                      <td className={styles.muted}>{item.unit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Section>

      <Section
        title="標準タスク"
        meta="原本02。案件を作ると、この定義から工程タスクが展開されます。"
        theme="company"
        actions={
          <select value={phaseId} onChange={(event) => setPhaseId(event.target.value)}>
            {(master?.phases ?? []).map((phase) => (
              <option key={phase.phaseId} value={phase.phaseId}>
                {phase.phaseId} {phase.name}（{phase.taskCount}件）
              </option>
            ))}
          </select>
        }
      >
        {tasks.length === 0 ? (
          <SkeletonRow />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>タスク</th>
                  <th>完了条件</th>
                  <th>適用条件</th>
                  <th>Gate</th>
                  <th>根拠</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.taskId}>
                    <td className={styles.taskId}>{task.taskId}</td>
                    <td>
                      {task.name}
                      <div className={styles.muted}>{task.description}</div>
                    </td>
                    <td className={styles.wrapText}>{task.completionCriteria}</td>
                    <td className={styles.muted}>{task.applicability}</td>
                    <td className={styles.taskId}>{task.gateId}</td>
                    <td className={styles.taskId}>{task.sourceIds.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Section
        title="標準開発ループ"
        meta="原本14。工程を横断して繰り返す8ステップ。AIと人の担当、止める条件を分けています。"
        theme="company"
      >
        {standards === null ? (
          <SkeletonRow />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>順</th>
                  <th>ステップ</th>
                  <th>入力・処理</th>
                  <th>AIの担当</th>
                  <th>人の担当</th>
                  <th>停止・差戻し</th>
                </tr>
              </thead>
              <tbody>
                {standards.devLoop.map((step) => (
                  <tr key={step.step}>
                    <td className={styles.taskId}>{step.step}</td>
                    <td>{step.name}</td>
                    <td className={styles.wrapText}>{step.input}</td>
                    <td className={styles.wrapText}>{step.aiRole}</td>
                    <td className={styles.wrapText}>{step.humanRole}</td>
                    <td className={styles.wrapText}>{step.stopCondition}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Section
        title="AI駆動開発の統制（A01〜A16）と実行設定"
        meta="原本14。宣言は実行認可ではありません。実行側で強制する項目を分けています。"
        theme="company"
      >
        {standards === null ? (
          <SkeletonRow />
        ) : (
          <>
            <div className={styles.tableWrap} style={{ marginBottom: 14 }}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>対象</th>
                    <th>標準</th>
                    <th>実施内容</th>
                    <th>証拠</th>
                    <th>関連Task</th>
                  </tr>
                </thead>
                <tbody>
                  {standards.harness.map((item) => (
                    <tr key={item.controlId}>
                      <td className={styles.taskId}>{item.controlId}</td>
                      <td className={styles.muted}>{item.target}</td>
                      <td>{item.standard}</td>
                      <td className={styles.wrapText}>{item.detail}</td>
                      <td className={styles.wrapText}>{item.evidence}</td>
                      <td className={styles.taskId}>{item.relatedTaskIds.join(", ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className={styles.note}>
              Agent/Skill実行設定（案件で実運用値を記入する項目）
              {standards.runtimeSettings.map((setting) => (
                <span key={setting.name}>
                  <br />
                  {setting.name} — {setting.check}
                </span>
              ))}
            </p>
          </>
        )}
      </Section>

      <Section
        title="負の試験（AT01〜AT07）"
        meta="原本14。v1.1で追加された実試験仕様です。表計算上の検査ではなく、実Agent・実環境で実施します。"
        theme="company"
      >
        {standards === null ? (
          <SkeletonRow />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>適用</th>
                  <th>試験テーマ</th>
                  <th>具体的な負の試験・受入条件</th>
                  <th>保存する証拠</th>
                  <th>関連Task</th>
                </tr>
              </thead>
              <tbody>
                {standards.harnessTests.map((test) => (
                  <tr key={test.testId}>
                    <td className={styles.taskId}>{test.testId}</td>
                    <td className={styles.muted}>{test.appliesWhen}</td>
                    <td>{test.theme}</td>
                    <td className={styles.wrapText}>{test.specification}</td>
                    <td className={styles.wrapText}>{test.evidence}</td>
                    <td className={styles.taskId}>{test.relatedTaskIds.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Section
        title="評価分類（E01〜E18）"
        meta="原本32。評価計画はこの分類から作ります。"
        theme="company"
      >
        {standards === null ? (
          <SkeletonRow />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>評価軸</th>
                  <th>指標候補</th>
                  <th>設計上の要点</th>
                  <th>適用条件</th>
                </tr>
              </thead>
              <tbody>
                {standards.evalTypes.map((item) => (
                  <tr key={item.evalTypeId}>
                    <td className={styles.taskId}>{item.evalTypeId}</td>
                    <td>{item.axis}</td>
                    <td className={styles.wrapText}>{item.metrics}</td>
                    <td className={styles.wrapText}>{item.designNote}</td>
                    <td className={styles.muted}>{item.applicability}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Section
        title="根拠にした資料"
        meta="原本24。各タスク・台帳の「根拠ID」はこの表を引きます。URLは参考情報で、自動更新しません。"
        theme="company"
      >
        {standards === null ? (
          <SkeletonRow />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>組織・資料</th>
                  <th>採用した内容</th>
                  <th>確認範囲・限界</th>
                  <th>確認日</th>
                </tr>
              </thead>
              <tbody>
                {standards.sources.map((source) => (
                  <tr key={source.sourceId}>
                    <td className={styles.taskId}>{source.sourceId}</td>
                    <td>
                      <div className={styles.muted}>{source.organization}</div>
                      {source.url.startsWith("http") ? (
                        <a href={source.url} target="_blank" rel="noreferrer">
                          {source.title}
                        </a>
                      ) : (
                        source.title
                      )}
                    </td>
                    <td className={styles.wrapText}>{source.adopted}</td>
                    <td className={styles.wrapText}>{source.limitation}</td>
                    <td className={styles.muted}>{source.checkedOn}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </>
  );
}
