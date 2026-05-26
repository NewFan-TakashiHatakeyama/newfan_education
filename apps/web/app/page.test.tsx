import React from "react";
import { render, screen } from "@testing-library/react";
import LandingPage from "./page";

describe("LandingPage", () => {
  it("renders LP sections from UI spec", () => {
    render(<LandingPage />);
    expect(screen.getByText("AI Field Ready")).toBeInTheDocument();
    expect(screen.getByText("案件要件→育成→証跡→提案の業務フロー")).toBeInTheDocument();
    expect(screen.getByText("育成ダッシュボードを見る")).toBeInTheDocument();
    expect(screen.getByText("ログイン")).toBeInTheDocument();
  });
});
