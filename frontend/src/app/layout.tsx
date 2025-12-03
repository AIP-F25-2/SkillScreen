import type { Metadata } from "next";
import { Questrial } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { CheatPreventionProvider } from "@/contexts/CheatPreventionContext";

const questrial = Questrial({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-questrial",
});

export const metadata: Metadata = {
  title: "SkillScreen",
  description: "AI-powered interview platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${questrial.className} min-h-screen bg-background text-foreground antialiased`}>
        <AuthProvider>
          <CheatPreventionProvider>
            {children}
          </CheatPreventionProvider>
        </AuthProvider>
      </body>
    </html>
  );
}