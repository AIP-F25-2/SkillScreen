import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const teamMembers = [
    {
        name: "Sheethal Shivakumar",
        role: "Project Manager & Team Lead",
        image: "/avatars/01.png",
        initials: "SS"
    },
    {
        name: "Chalithya Sangeeth",
        role: "Technical Lead & Full-stack Dev",
        image: "/avatars/02.png",
        initials: "CS"
    },
    {
        name: "Dimantha Kalhara",
        role: "Full-Stack Dev(Frontend/ UI/UX Focus)",
        image: "/avatars/03.png",
        initials: "DK"
    },
    {
        name: "Mukul Garg",
        role: "Full-Stack Dev(Backend Focus)",
        image: "/avatars/04.png",
        initials: "MG"
    },
    {
        name: "Moksh Jaiswal",
        role: "ML Engineer",
        image: "/avatars/05.png",
        initials: "MJ"
    },
    {
        name: "Subhash Somarouthu",
        role: "ML Engineer",
        image: "/avatars/06.png",
        initials: "SS"
    },
    {
        name: "Yugahang Limbu",
        role: "Data Engineer & Database Administrator",
        image: "/avatars/07.png",
        initials: "YL"
    },
    {
        name: "Ashish Lama",
        role: "Full-Stack (Integration) & DevOps/QA Specialist",
        image: "/avatars/08.png",
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
                    <p className="text-lg text-indigo-200/80 max-w-2xl mx-auto">
                        The talented individuals behind SkillScreen.
                    </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 justify-items-center">
                    {teamMembers.map((member, index) => (
                        <Card key={index} className="w-full max-w-sm bg-indigo-950/20 border-indigo-500/20 backdrop-blur-sm hover:bg-indigo-900/30 transition-all duration-300 group">
                            <CardHeader className="text-center pb-2">
                                <div className="mx-auto mb-4 w-24 h-24 rounded-full overflow-hidden ring-2 ring-indigo-500/30 ring-offset-2 ring-offset-transparent group-hover:ring-indigo-400 transition-all">
                                    <Avatar className="w-full h-full">
                                        <AvatarImage src={member.image} alt={member.name} />
                                        <AvatarFallback className="bg-indigo-900/50 text-indigo-200 text-xl">
                                            {member.initials}
                                        </AvatarFallback>
                                    </Avatar>
                                </div>
                                <CardTitle className="text-xl font-semibold text-white group-hover:text-indigo-200 transition-colors">{member.name}</CardTitle>
                                <CardDescription className="text-indigo-300/80 font-medium mt-2">{member.role}</CardDescription>
                            </CardHeader>
                            <CardContent className="text-center">
                                {/* Add social links or bio here if needed */}
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>

            {/* Background decoration */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-600/10 rounded-full blur-3xl -z-10" />
        </section>
    );
}
