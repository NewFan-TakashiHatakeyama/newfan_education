import React from "react";
import { render, screen } from "@testing-library/react";
import LandingPage from "./page";

describe("LandingPage", () => {
  it("renders Enterprise LP sections", () => {
    render(<LandingPage />);
    expect(screen.getAllByText("AI Field Ready Enterprise").length).toBeGreaterThan(0);
    expect(
      screen.getByText("AI研修を実施しても、現場のAIプロジェクトが生まれない理由")
    ).toBeInTheDocument();
    expect(screen.getAllByText("AI人材育成診断を相談する").length).toBeGreaterThan(0);
    expect(screen.getByText("ログイン")).toBeInTheDocument();
  });
});
