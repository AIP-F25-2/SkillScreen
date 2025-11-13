'use client';

import { MacbookScrollMulti } from '@/components/ui/macbook-scroll-multi';

export function MacbookScrollDemo() {
  const sections = [
    {
      src: '/images/image.png', // You can replace with actual screenshots
      title: (
        <span>
          AI-Powered Interview Platform <br /> Revolutionize your hiring process
        </span>
      ),
      description: 'Automated resume parsing and candidate screening',
    },
    {
      src: '/images/image.png', // Replace with different screenshot
      title: (
        <span>
          Real-Time Code Analysis <br /> Evaluate technical skills instantly
        </span>
      ),
      description: 'Live coding assessments with instant feedback',
    },
    {
      src: '/images/image.png', // Replace with different screenshot
      title: (
        <span>
          Comprehensive Analytics <br /> Make data-driven hiring decisions
        </span>
      ),
      description: 'Track candidate performance and interview metrics',
    },
  ];

  return (
    <div className="w-full overflow-hidden bg-transparent dark:bg-transparent">
      <MacbookScrollMulti
        sections={sections}
        showGradient={false}
      />
    </div>
  );
}

