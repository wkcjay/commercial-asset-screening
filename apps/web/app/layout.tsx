import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Site Screening Copilot",
  description: "Grounded site screening dashboard for Singapore residential reference locations.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
