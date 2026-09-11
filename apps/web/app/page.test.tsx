import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import LandingPage from "./page";

describe("LandingPage", () => {
 it("connects training to implementation with working example selection and registration links", () => {
  render(<LandingPage />);
  expect(screen.getByRole('heading', {level:1})).toHaveTextContent('AIを学び、つくり、');
  expect(screen.getByRole('img', {name:/AIを学ぶ受講者/})).toBeInTheDocument();
  for (const link of screen.getAllByRole('link', {name:/法人利用を始める/})) expect(link).toHaveAttribute('href','/business/sign-up');
  expect(screen.getByRole('link', {name:/活用イメージを見る/})).toHaveAttribute('href','#examples');
  const search = screen.getByRole('button', {name:'社内ナレッジ検索'});
  fireEvent.click(search);
  expect(search).toHaveAttribute('aria-pressed','true');
  expect(screen.getByText('出張の申請手順を知りたいです。')).toBeInTheDocument();
  expect(screen.queryByText('製品の設定方法を教えてください。')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:'書類の読み取り・確認'}));
  expect(screen.getByText('この請求書の内容を整理してください。')).toBeInTheDocument();
 });
});
