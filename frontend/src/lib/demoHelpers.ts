/**
 * Demo Helper Functions
 * Provides dummy data for demonstration purposes
 */

export interface DemoJobDescription {
  title: string;
  company: string;
  description: string;
  required_skills: string[];
  experience_level: string;
}

/**
 * Get a demo job description based on skills found in resume
 * Falls back to a generic full-stack developer role
 */
export function getDemoJobDescription(resumeSkills?: string[]): DemoJobDescription {
  // Analyze skills to determine best fit job type
  const skillsLower = resumeSkills?.map(s => s.toLowerCase()) || [];
  
  // Check for frontend skills
  const hasFrontend = skillsLower.some(s => 
    ['react', 'vue', 'angular', 'javascript', 'typescript', 'html', 'css', 'frontend'].includes(s)
  );
  
  // Check for backend skills
  const hasBackend = skillsLower.some(s => 
    ['python', 'java', 'node', 'express', 'django', 'flask', 'fastapi', 'backend', 'api'].includes(s)
  );
  
  // Check for data science skills
  const hasDataScience = skillsLower.some(s => 
    ['machine learning', 'ml', 'data science', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'ai'].includes(s)
  );
  
  // Check for devops skills
  const hasDevOps = skillsLower.some(s => 
    ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'devops', 'ci/cd', 'jenkins'].includes(s)
  );

  // Return appropriate job based on skills
  if (hasDataScience) {
    return {
      title: "Senior Machine Learning Engineer",
      company: "TechVision AI",
      description: `We are seeking a talented Senior Machine Learning Engineer to join our innovative AI team. 
      
      **Responsibilities:**
      - Design and implement machine learning models for production systems
      - Work with large-scale datasets to train and evaluate models
      - Collaborate with cross-functional teams to deploy ML solutions
      - Research and implement state-of-the-art ML algorithms
      - Optimize model performance and scalability
      
      **Requirements:**
      - 5+ years of experience in machine learning and data science
      - Strong proficiency in Python, TensorFlow, and PyTorch
      - Experience with deep learning, NLP, or computer vision
      - Knowledge of MLOps and model deployment best practices
      - Strong problem-solving and analytical skills
      
      **Nice to Have:**
      - Experience with cloud platforms (AWS, GCP, Azure)
      - Publications in ML conferences or journals
      - Contributions to open-source ML projects`,
      required_skills: [
        'Python', 'Machine Learning', 'TensorFlow', 'PyTorch', 'Deep Learning',
        'NLP', 'Computer Vision', 'Pandas', 'NumPy', 'Scikit-learn', 'MLOps',
        'AWS', 'Docker', 'Kubernetes', 'Data Analysis'
      ],
      experience_level: "senior"
    };
  }
  
  if (hasDevOps) {
    return {
      title: "DevOps Engineer",
      company: "CloudScale Solutions",
      description: `Join our DevOps team to build and maintain world-class infrastructure and deployment pipelines.
      
      **Responsibilities:**
      - Design and implement CI/CD pipelines
      - Manage cloud infrastructure on AWS/Azure/GCP
      - Containerize applications using Docker and Kubernetes
      - Monitor system performance and implement improvements
      - Ensure security and compliance across infrastructure
      
      **Requirements:**
      - 3+ years of DevOps or infrastructure experience
      - Strong knowledge of Docker and Kubernetes
      - Experience with cloud platforms (AWS, Azure, or GCP)
      - Proficiency in scripting (Bash, Python, or Go)
      - Understanding of infrastructure as code (Terraform, Ansible)
      
      **Nice to Have:**
      - Experience with service mesh (Istio, Linkerd)
      - Knowledge of monitoring tools (Prometheus, Grafana)
      - Security certifications`,
      required_skills: [
        'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'CI/CD', 'Jenkins',
        'Terraform', 'Ansible', 'Python', 'Bash', 'Linux', 'DevOps',
        'Monitoring', 'Security'
      ],
      experience_level: "mid"
    };
  }
  
  if (hasFrontend && hasBackend) {
    return {
      title: "Full Stack Developer",
      company: "InnovateTech",
      description: `We're looking for a versatile Full Stack Developer to build amazing web applications from front to back.
      
      **Responsibilities:**
      - Develop responsive web applications using modern frameworks
      - Build and maintain RESTful APIs and microservices
      - Collaborate with designers to implement pixel-perfect UIs
      - Write clean, maintainable, and well-tested code
      - Participate in code reviews and technical discussions
      
      **Requirements:**
      - 3+ years of full-stack development experience
      - Strong proficiency in React, TypeScript, and Node.js
      - Experience with Python, FastAPI, or Django
      - Knowledge of SQL and NoSQL databases
      - Understanding of modern development practices
      
      **Nice to Have:**
      - Experience with Next.js or other SSR frameworks
      - Knowledge of GraphQL
      - Experience with cloud deployment
      - Contributions to open-source projects`,
      required_skills: [
        'React', 'TypeScript', 'JavaScript', 'Node.js', 'Python', 'FastAPI',
        'Django', 'PostgreSQL', 'MongoDB', 'REST API', 'Git', 'Docker',
        'HTML', 'CSS', 'Tailwind'
      ],
      experience_level: "mid"
    };
  }
  
  if (hasFrontend) {
    return {
      title: "Frontend Developer",
      company: "UX Masters",
      description: `Join our frontend team to create beautiful, performant user interfaces.
      
      **Responsibilities:**
      - Build responsive and accessible web applications
      - Implement designs with attention to detail
      - Optimize application performance
      - Work closely with designers and backend developers
      - Write reusable and maintainable components
      
      **Requirements:**
      - 2+ years of frontend development experience
      - Expert knowledge of React and TypeScript
      - Strong understanding of HTML, CSS, and JavaScript
      - Experience with state management (Redux, Zustand)
      - Knowledge of modern build tools and workflows
      
      **Nice to Have:**
      - Experience with Next.js or Remix
      - Knowledge of animation libraries (Framer Motion, GSAP)
      - Understanding of web accessibility (WCAG)`,
      required_skills: [
        'React', 'TypeScript', 'JavaScript', 'HTML', 'CSS', 'Tailwind',
        'Redux', 'Next.js', 'Webpack', 'Git', 'REST API', 'Responsive Design'
      ],
      experience_level: "mid"
    };
  }
  
  if (hasBackend) {
    return {
      title: "Backend Developer",
      company: "ScaleTech",
      description: `We need a skilled Backend Developer to build robust and scalable server-side applications.
      
      **Responsibilities:**
      - Design and implement RESTful APIs
      - Build microservices architecture
      - Optimize database queries and performance
      - Ensure application security and data protection
      - Write comprehensive tests and documentation
      
      **Requirements:**
      - 3+ years of backend development experience
      - Strong proficiency in Python and FastAPI/Django
      - Experience with PostgreSQL or MySQL
      - Knowledge of caching strategies (Redis)
      - Understanding of API design best practices
      
      **Nice to Have:**
      - Experience with message queues (RabbitMQ, Kafka)
      - Knowledge of microservices patterns
      - Experience with AWS or other cloud platforms`,
      required_skills: [
        'Python', 'FastAPI', 'Django', 'PostgreSQL', 'MySQL', 'Redis',
        'REST API', 'Microservices', 'Docker', 'Git', 'SQL', 'API Design'
      ],
      experience_level: "mid"
    };
  }
  
  // Default: Generic Software Engineer
  return {
    title: "Software Engineer",
    company: "TechCorp",
    description: `Join our engineering team to build innovative software solutions.
    
    **Responsibilities:**
    - Design, develop, and maintain software applications
    - Collaborate with cross-functional teams
    - Write clean, efficient, and well-documented code
    - Participate in code reviews and technical discussions
    - Stay updated with emerging technologies
    
    **Requirements:**
    - Bachelor's degree in Computer Science or related field
    - 2+ years of software development experience
    - Proficiency in at least one programming language
    - Strong problem-solving skills
    - Good communication and teamwork abilities
    
    **Nice to Have:**
    - Experience with cloud platforms
    - Knowledge of agile methodologies
    - Contributions to open-source projects`,
    required_skills: [
      'Programming', 'Problem Solving', 'Git', 'Algorithms', 'Data Structures',
      'Software Design', 'Testing', 'Debugging'
    ],
    experience_level: "mid"
  };
}

/**
 * Get demo interview questions for testing (fallback if AI service is unavailable)
 */
export function getDemoInterviewQuestions() {
  return [
    {
      id: 'demo-q1',
      question_index: 0,
      question_text: "Tell me about yourself and your professional background.",
      question_type: "general",
      difficulty: "easy",
      round_number: 1
    },
    {
      id: 'demo-q2',
      question_index: 1,
      question_text: "What are your key strengths and how do they apply to this role?",
      question_type: "general",
      difficulty: "easy",
      round_number: 1
    },
    {
      id: 'demo-q3',
      question_index: 2,
      question_text: "Describe a challenging project you've worked on recently and how you approached it.",
      question_type: "general",
      difficulty: "medium",
      round_number: 1
    },
    {
      id: 'demo-q4',
      question_index: 3,
      question_text: "Walk me through your technical experience and the technologies you've worked with.",
      question_type: "technical",
      difficulty: "medium",
      round_number: 2
    },
    {
      id: 'demo-q5',
      question_index: 4,
      question_text: "How do you approach debugging and troubleshooting technical issues?",
      question_type: "technical",
      difficulty: "medium",
      round_number: 2
    },
    {
      id: 'demo-q6',
      question_index: 5,
      question_text: "Describe your experience with version control and collaborative development.",
      question_type: "technical",
      difficulty: "easy",
      round_number: 2
    },
    {
      id: 'demo-q7',
      question_index: 6,
      question_text: "What are the best practices you follow in your development work?",
      question_type: "theoretical",
      difficulty: "medium",
      round_number: 3
    },
    {
      id: 'demo-q8',
      question_index: 7,
      question_text: "How do you ensure code quality and maintainability in your projects?",
      question_type: "theoretical",
      difficulty: "hard",
      round_number: 3
    },
    {
      id: 'demo-q9',
      question_index: 8,
      question_text: "What industry trends do you think will shape the future of software development?",
      question_type: "theoretical",
      difficulty: "medium",
      round_number: 3
    }
  ];
}

