import type { Metadata } from "next";
import { AppThemeProvider } from "@/components/AppThemeProvider";
import AuthGate from "@/components/auth/AuthGate";

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
        <AuthGate>
          <AppThemeProvider>{children}</AppThemeProvider>
        </AuthGate>
      </body>
    </html>
  );
}
