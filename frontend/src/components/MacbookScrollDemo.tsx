'use client';

import { MacbookScrollMulti } from '@/components/ui/macbook-scroll-multi';

export function MacbookScrollDemo() {
  const sections = [
    {
      src: 'https://images.unsplash.com/photo-1557425493-6f90ae4659fc?w=800&h=600&fit=crop',
      title: 'AI-Powered Interview Platform',
      description: 'Revolutionize your hiring process with automated resume parsing and intelligent candidate screening',
    },
    {
      src: 'https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=800&h=600&fit=crop',
      title: 'Real-Time Code Analysis',
      description: 'Evaluate technical skills instantly with live coding assessments and automatic feedback',
    },
    {
      src: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=600&fit=crop',
      title: 'Comprehensive Analytics',
      description: 'Make data-driven hiring decisions by tracking candidate performance and interview metrics',
    },
    {
      src: 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&h=600&fit=crop',
      title: 'Collaborative Hiring',
      description: 'Enable your team to review candidates together with shared notes and real-time collaboration tools',
    },
    {
      src: 'https://images.unsplash.com/photo-1552664730-d307ca884978?w=800&h=600&fit=crop',
      title: 'Video Interview Recording',
      description: 'Record and replay interviews to ensure you never miss important details and can share with stakeholders',
    },
    {
      src: 'https://images.unsplash.com/photo-1551434678-e076c223a692?w=800&h=600&fit=crop',
      title: 'Customizable Assessments',
      description: 'Create tailored interview questions and coding challenges specific to your role requirements',
    },
    {
      src: 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800&h=600&fit=crop',
      title: 'Candidate Experience Portal',
      description: 'Provide candidates with a seamless experience from application to offer with transparent communication',
    },
  ];

  return (
    <MacbookScrollMulti
      sections={sections}
      showGradient={false}
    />
  );
}

