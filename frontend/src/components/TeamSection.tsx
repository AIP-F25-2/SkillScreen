import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const teamMembers = [
    {
        name: "Sheethal Shivakumar",
        role: "Project Manager & Team Lead",
        image: "/avatars/Sheethal.png",
        initials: "SS"
    },
    {
        name: "Chalithya Sangeeth",
        role: "Technical Lead & Full-stack Dev",
        image: "/avatars/Sangeeth.jpeg",
        initials: "CS"
    },
    {
        name: "Dimantha Goonewardena",
        role: "Full-Stack Dev(Frontend/ UI/UX Focus)",
        image: "/avatars/Dimantha.png",
        initials: "DK"
    },
    {
        name: "Mukul Garg",
        role: "Full-Stack Dev(Backend Focus)",
        image: "/avatars/Mukul.JPG",
        initials: "MG"
    },
    {
        name: "Moksh Jaiswal",
        role: "ML Engineer",
        image: "/avatars/Moksh.jpeg",
        initials: "MJ"
    },
    {
        name: "Subhash Somarouthu",
        role: "ML Engineer",
        image: "/avatars/Subhash.png",
        initials: "SS"
    },
    {
        name: "Yugahang Limbu",
        role: "Data Engineer & Database Administrator",
        image: "/avatars/Yugahang.jpeg",
        initials: "YL"
    },
    {
        name: "Ashish Lama",
        role: "Full-Stack (Integration) & DevOps/QA Specialist",
        image: "/avatars/Ashish.jpeg",
        initials: "AL"
    },
];

export function TeamSection() {
    return (
        <section className="py-24 relative overflow-hidden">
            <div className="container mx-auto px-4 md:px-6 relative z-10">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 to-white mb-4">
                        Meet Our Team
                    </h2>
                    <p className="text-2xl text-white-200/80 max-w-2xl mx-auto font-bold">
                        The talented individuals behind SkillScreen.
                    </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 justify-items-center">
                    {teamMembers.map((member) => (
                        <Card key={member.name} className="bg-[#020617] border-white/10 overflow-hidden hover:border-indigo-500/50 transition-all duration-300 group flex flex-col relative shrink-0 shadow-lg shadow-black/50 w-[280px] h-[420px]">
                            <CardHeader className="text-center p-8 h-full flex flex-col items-center justify-start pt-10">
                                <div className="mb-6 w-32 h-32 rounded-full overflow-hidden ring-4 ring-indigo-500/20 group-hover:ring-indigo-500/50 transition-all shrink-0 shadow-[0_0_20px_rgba(99,102,241,0.3)] group-hover:shadow-[0_0_30px_rgba(99,102,241,0.5)]">
                                    <Avatar className="w-full h-full">
                                        <AvatarImage src={member.image} alt={member.name} className="object-cover w-full h-full" />
                                        <AvatarFallback className="bg-indigo-950 text-indigo-200 text-xl">
                                            {member.initials}
                                        </AvatarFallback>
                                    </Avatar>
                                </div>
                                <CardTitle className="text-xl font-bold text-white group-hover:text-indigo-200 transition-colors min-h-[3.5rem] flex items-center justify-center leading-tight w-full">{member.name}</CardTitle>
                                <CardDescription className="text-slate-400 font-medium mt-2 h-[5rem] flex items-start justify-center leading-tight w-full overflow-hidden text-sm">{member.role}</CardDescription>
                            </CardHeader>
                        </Card>
                    ))}

                </div>
            </div>

            {/* Background decoration */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-600/10 rounded-full blur-3xl -z-10" />
        </section >
    );
}
