import React, { Suspense } from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { VentureLedgerEntry, VentureLedgerSummary } from "@newfan/contracts";
import LedgerPage from "./[ventureId]/ledgers/[ledgerKey]/page";
import { DecisionPanel } from "./DecisionPanel";
import { EvaluationCoverage } from "./EvaluationCoverage";
import styles from "./ventures.module.css";

const api = vi.hoisted(() => ({ fetchVentureLedger: vi.fn(), saveVentureLedgerEntry: vi.fn() }));
vi.mock("@/lib/api", () => api);
vi.mock("./useVentureRole", () => ({ useVentureRole: () => ({ canEdit: true, canVerify: true, roleIds: ["R19"] }) }));
vi.mock("./VentureNav", () => ({ VentureNav: () => null }));
vi.mock("@/app/components/ui/Section", () => ({ Section: ({ title, children, actions }: { title: string; children: React.ReactNode; actions: React.ReactNode }) => <section><h2>{title}</h2>{actions}{children}</section> }));
vi.mock("@/app/components/ui/Drawer", () => ({ Drawer: ({ open, children, footer }: { open: boolean; children: React.ReactNode; footer?: React.ReactNode }) => open ? <aside>{children}{footer}</aside> : null }));

const entry = (index: number): VentureLedgerEntry => ({
  revision: "original",
  id: `row-${index}`, rowKey: `PLAN-${index}`, isMasterRow: true, status: "未着手", master: {},
  values: { EvalType: "E01" }, derived: { 点検: "決裁整合未充足" },
  checks: { 点検: { code: "not-ready", severity: "warning", label: "決裁整合未充足" } },
  updatedBy: null, updatedByName: "", updatedAt: null
});
const data = (count = 1): VentureLedgerSummary => ({ ledger: {
  key: "eval_plan", name: "評価計画", summary: "評価の版と分類", sourceSheet: "15", idColumn: "EvalType",
  seeded: true, masterColumns: [], inputColumns: ["EvalType"], notes: [],
  columnRules: { EvalType: { type: "select", options: ["E01", "E05"] } }, derivedColumns: [],
  checkColumns: ["点検"], rowLimit: null, stateColumn: "状態", lockedStates: [], masterRowCount: 18
}, items: Array.from({ length: count }, (_, i) => entry(i)) });
async function openPage() {
  const params = Promise.resolve({ ventureId: "v", ledgerKey: "eval_plan" });
  await act(async () => { render(<Suspense fallback="loading"><LedgerPage params={params} /></Suspense>); });
  await screen.findByText("評価計画");
}
beforeEach(() => { vi.clearAllMocks(); api.fetchVentureLedger.mockResolvedValue(data()); });

describe("venture governance UI", () => {
  it("shows all missing classifications before any evaluation is registered", () => {
    render(<EvaluationCoverage entries={[]} />);
    expect(screen.getAllByText(/E\d{2}：未判定/)).toHaveLength(18);
  });
  it("keeps negative verdicts out of the success style", async () => {
    await openPage();
    expect(screen.getByText("決裁整合未充足")).toHaveClass(styles.pillProgress);
    expect(screen.getByText("決裁整合未充足")).not.toHaveClass(styles.pillDone);
  });

  it("allows adding to seeded ledgers and pages beyond 25 rows", async () => {
    api.fetchVentureLedger.mockResolvedValue(data(26));
    await openPage();
    expect(screen.getByRole("button", { name: "行を追加" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "PLAN-25" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "次の25件" }));
    expect(screen.getByRole("button", { name: "PLAN-25" })).toBeInTheDocument();
  });

  it("retains a failed save and prevents verification of an unsaved draft", async () => {
    api.saveVentureLedgerEntry.mockRejectedValue(new Error("保存に失敗"));
    await openPage();
    fireEvent.click(screen.getByRole("button", { name: "PLAN-0" }));
    fireEvent.change(screen.getByLabelText("EvalType"), { target: { value: "E05" } });
    expect(screen.getByRole("button", { name: "保存内容を独立確認" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "保存する" }));
    await screen.findAllByText("保存に失敗");
    expect(screen.getByLabelText("EvalType")).toHaveValue("E05");
    await waitFor(() => expect(api.saveVentureLedgerEntry).toHaveBeenCalledWith("v", "eval_plan", { id: "row-0", expectedRevision: "original", values: { EvalType: "E05" } }));
  });

  it("compares a conflicting revision and retains the user's edit for an explicit merge", async () => {
    await openPage();
    fireEvent.click(screen.getByRole("button", { name: "PLAN-0" }));
    fireEvent.change(screen.getByLabelText("EvalType"), { target: { value: "E05" } });
    api.saveVentureLedgerEntry.mockRejectedValue(new Error("更新が競合しました"));
    const latest = data(); latest.items[0] = {...latest.items[0], revision: "new", values: {EvalType: "E01", "正本ID": "latest source"}};
    api.fetchVentureLedger.mockResolvedValue(latest);
    fireEvent.click(screen.getByRole("button", { name: "保存する" }));
    await screen.findByText("最新の保存内容");
    expect(screen.getByLabelText("EvalType")).toHaveValue("E05");
    fireEvent.click(screen.getByRole("button", {name: "自分の変更を保持して最新の版へ反映"}));
    api.saveVentureLedgerEntry.mockResolvedValue({...latest.items[0], values: {EvalType: "E05", "正本ID": "latest source"}});
    fireEvent.click(screen.getByRole("button", {name: "保存する"}));
    await waitFor(() => expect(api.saveVentureLedgerEntry).toHaveBeenLastCalledWith("v", "eval_plan", {
      id: "row-0", expectedRevision: "new", values: {EvalType: "E05", "正本ID": "latest source"}
    }));
  });

  it("uses the new revision after a status change without discarding field edits", async () => {
    await openPage();
    fireEvent.click(screen.getByRole("button", { name: "PLAN-0" }));
    fireEvent.change(screen.getByLabelText("EvalType"), { target: { value: "E05" } });
    api.saveVentureLedgerEntry.mockResolvedValue({...entry(0), status: "確認中", revision: "status-revision"});
    fireEvent.change(screen.getByLabelText("状態"), {target: {value: "確認中"}});
    await waitFor(() => expect(screen.getByLabelText("状態")).toHaveValue("確認中"));
    expect(screen.getByLabelText("EvalType")).toHaveValue("E05");
    fireEvent.click(screen.getByRole("button", {name: "保存する"}));
    await waitFor(() => expect(api.saveVentureLedgerEntry).toHaveBeenLastCalledWith("v", "eval_plan", {
      id: "row-0", expectedRevision: "status-revision", values: {EvalType: "E05"}
    }));
  });

  it("shows overdue decisions and unknown investment balances", () => {
    render(<DecisionPanel ventureId="v" decisions={{ riskState: "再判定待ち", hypotheses: [{ id: "HY01", values: { "次の実験": "有償継続の検証" }, checks: { "追加投資残額（円）": "未計測" } }], kpis: [], conditions: [], cashPlans: [], runs: [],
      nextActions: [{ ledgerKey: "hypothesis", rowId: "HY01", dueDate: "2026-09-01", overdue: true, action: "有償継続の検証", owner: "PdM" }] }} />);
    expect(screen.getByText(/期限超過・再審査要/)).toBeInTheDocument();
    expect(screen.getAllByText("未計測").length).toBeGreaterThan(0);
    expect(screen.getByText("リスク前提：再判定待ち")).toBeInTheDocument();
  });
});
