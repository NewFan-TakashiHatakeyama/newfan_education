import "./globals.css";
import type { ReactNode } from "react";
import { Poppins } from "next/font/google";
import { AppShell } from "./components/AppShell";

const poppins = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"]
});

export const metadata = {
  title: "Newfan Education",
  description: "Priority settings implementation sandbox"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body className={poppins.className}>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
