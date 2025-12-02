import { Questrial } from "next/font/google";

const questrial = Questrial({
    subsets: ["latin"],
    weight: "400",
    variable: "--font-questrial",
});

export default function PortfolioLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className={`${questrial.className} ${questrial.variable}`}>
            {children}
        </div>
    );
}
