import type { Metadata } from "next";
import { AppThemeProvider } from "@/components/AppThemeProvider";

export const metadata: Metadata = {
  title: "HireLens AI",
  description: "AI-powered recruitment screening platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppThemeProvider>{children}</AppThemeProvider>
      </body>
    </html>
  );
}
