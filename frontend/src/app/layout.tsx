import type { Metadata } from "next";
import { AppThemeProvider } from "@/components/AppThemeProvider";
import AuthGate from "@/components/auth/AuthGate";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "HireLens AI",
    template: "%s | HireLens AI",
  },
  description:
    "Explainable AI-powered recruitment screening workspace.",
  icons: {
    icon: [
      {
        url: "https://icons.iconarchive.com/icons/google/noto-emoji-objects/128/62915-briefcase-icon.png",
        type: "image/png",
        sizes: "128x128",
      },
    ],
    apple:
      "https://icons.iconarchive.com/icons/google/noto-emoji-objects/128/62915-briefcase-icon.png",
  },
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
          <AppThemeProvider>
            {children}
          </AppThemeProvider>
        </AuthGate>
      </body>
    </html>
  );
}