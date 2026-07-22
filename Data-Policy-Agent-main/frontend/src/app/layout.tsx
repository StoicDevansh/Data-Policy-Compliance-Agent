import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Data Policy Agent | BeyondInfinity",
  description: "Automated, Explainable & Continuous Compliance Monitoring",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
