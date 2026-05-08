import type { Metadata } from "next";
import { AuthProvider } from "@/lib/auth-context";
import { OrgProvider } from "@/lib/org-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "MegaIoT Platform",
  description: "AI-native IoT platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased selection:bg-primary/30">
        <AuthProvider>
          <OrgProvider>
            {children}
          </OrgProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
