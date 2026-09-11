import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import LandingPage from "./page";

describe("LandingPage", () => {
  it("renders Enterprise LP sections", () => {
    render(<LandingPage />);
    expect(screen.getAllByText("AI Field Ready Enterprise").length).toBeGreaterThan(0);
    expect(
      screen.getByText("AI研修をしても、現場のAIプロジェクトが生まれない理由")
    ).toBeInTheDocument();
    expect(screen.getAllByText("AI人材育成診断を相談する").length).toBeGreaterThan(0);
    expect(screen.getByText("問い合わせ回答支援AI")).toBeInTheDocument();
    expect(screen.getByText("回答ドラフト例")).toBeInTheDocument();
    expect(screen.getByText("返品・交換")).toBeInTheDocument();
    expect(screen.getByText("補償判断")).toBeInTheDocument();
    expect(screen.getByText("ログイン（学習者・企業）")).toBeInTheDocument();
    expect(screen.getByText("問い合わせ回答支援AIの操作感")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /業務課題登録/ })).toBeInTheDocument();
    expect(screen.getByText("根拠付きドラフト → 人が最終確認")).toBeInTheDocument();
  });
});
