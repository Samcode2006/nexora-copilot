import type {
  StudentProfile,
  Job,
  Application,
  ResumeDocument,
  ResumeDraft,
  CoverLetterDraft,
  ApprovalItem,
  CalendarEvent,
  InterviewSession,
  FeedbackReport,
  RoadmapTask,
  FollowUpItem,
  AssistantChatMessage
} from '../types';

export const initialProfile: StudentProfile = {
  id: 'student-aarav-01',
  fullName: 'Aarav Sharma',
  email: 'aarav.sharma@university.edu',
  phone: '+91 98765 43210',
  college: 'National Institute of Technology, Tiruchirappalli',
  degree: 'Bachelor of Technology',
  branch: 'Computer Science and Engineering',
  graduationYear: '2027',
  currentYear: 'Final Year (4th Year)',
  location: 'Bangalore / Chennai / Remote',
  bio: 'Computer Science undergraduate passionate about building resilient distributed web systems, clean interfaces, and developer tooling. Looking for high-impact software engineering roles.',
  completeness: 88,
  links: {
    github: 'https://github.com/aaravsharma-dev',
    linkedin: 'https://linkedin.com/in/aarav-sharma-tech',
    portfolio: 'https://aaravsharma.dev'
  },
  skills: [
    { id: 'sk-1', name: 'TypeScript', category: 'frontend', level: 'Advanced', verified: true },
    { id: 'sk-2', name: 'React', category: 'frontend', level: 'Advanced', verified: true },
    { id: 'sk-3', name: 'Node.js', category: 'backend', level: 'Intermediate', verified: true },
    { id: 'sk-4', name: 'PostgreSQL', category: 'data', level: 'Intermediate', verified: true },
    { id: 'sk-5', name: 'Tailwind CSS', category: 'frontend', level: 'Advanced', verified: true },
    { id: 'sk-6', name: 'REST APIs', category: 'backend', level: 'Advanced', verified: true },
    { id: 'sk-7', name: 'Docker', category: 'tools', level: 'Intermediate', verified: false },
    { id: 'sk-8', name: 'Git & GitHub', category: 'tools', level: 'Advanced', verified: true },
    { id: 'sk-9', name: 'Python', category: 'core', level: 'Intermediate', verified: true },
    { id: 'sk-10', name: 'Data Structures & Algorithms', category: 'core', level: 'Advanced', verified: true },
  ],
  education: [
    {
      id: 'edu-1',
      institution: 'National Institute of Technology, Tiruchirappalli',
      degree: 'B.Tech in Computer Science and Engineering',
      field: 'Computer Science',
      startYear: '2023',
      endYear: '2027',
      grade: '8.84 CGPA'
    },
    {
      id: 'edu-2',
      institution: 'Delhi Public School, R.K. Puram',
      degree: 'Senior Secondary (Class XII CBSE)',
      field: 'Science (PCM & CS)',
      startYear: '2021',
      endYear: '2023',
      grade: '96.2%'
    }
  ],
  experience: [
    {
      id: 'exp-1',
      role: 'Software Engineering Intern',
      company: 'InnovateCloud Labs',
      location: 'Bangalore (Hybrid)',
      startDate: 'May 2026',
      endDate: 'Jul 2026',
      current: false,
      description: 'Worked with the core platform team developing internal telemetry services and microservices.',
      highlights: [
        'Built telemetry aggregation pipeline processing 250k daily events using Node.js and Redis cache.',
        'Reduced p95 dashboard response latencies by 38% through PostgreSQL query index redesign.',
        'Authored 14 end-to-end integration test suites ensuring zero regression during major API v2 rollout.'
      ]
    }
  ],
  projects: [
    {
      id: 'proj-1',
      title: 'Resilient Distributed Task Runner',
      description: 'Lightweight asynchronous background task orchestrator with retry strategies and queue visualizer.',
      technologies: ['TypeScript', 'Node.js', 'Redis', 'PostgreSQL', 'Docker'],
      role: 'Lead Architect',
      highlights: [
        'Implemented exponential backoff retry mechanism with dead-letter queue processing.',
        'Integrated live status dashboard using Server-Sent Events (SSE) supporting 1,000+ concurrent workers.',
        'Open-sourced on GitHub with 140+ stars and full containerized local testing environment.'
      ],
      github: 'https://github.com/aaravsharma-dev/task-runner'
    },
    {
      id: 'proj-2',
      title: 'Campus Peer Marketplace',
      description: 'Full-stack platform for verified campus students to trade course books, project gear, and notes.',
      technologies: ['React', 'TypeScript', 'Tailwind CSS', 'Supabase', 'Node.js'],
      role: 'Full Stack Developer',
      highlights: [
        'Used college institutional email SSO for verification, onboarding 1,400+ active campus peers.',
        'Designed accessible responsive UI with shadcn/ui and optimized client-side search indexing.'
      ],
      link: 'https://campus-peer-trade.preview.dev'
    }
  ],
  certifications: [
    {
      id: 'cert-1',
      title: 'AWS Certified Cloud Practitioner',
      issuer: 'Amazon Web Services',
      issueDate: 'Aug 2026',
      credentialUrl: 'https://aws.amazon.com/verification'
    },
    {
      id: 'cert-2',
      title: 'Meta Frontend Developer Professional Certificate',
      issuer: 'Coursera / Meta',
      issueDate: 'Jan 2026',
      credentialUrl: 'https://coursera.org/verify/professional-cert'
    }
  ],
  preferences: {
    targetRoles: ['Software Engineer Intern', 'Frontend Engineer', 'Full Stack Developer'],
    preferredDomains: ['Cloud Infrastructure', 'Developer Tools', 'Fintech', 'Enterprise SaaS'],
    preferredLocations: ['Bangalore', 'Hyderabad', 'Remote', 'Chennai'],
    employmentType: 'Both',
    workMode: 'Hybrid',
    skillsOfInterest: ['Distributed Systems', 'Apache Kafka', 'GraphQL', 'Kubernetes'],
    companyTypes: ['High-growth Product Startups', 'Established Tech Giants', 'Developer Platforms'],
    minStipendSalary: '₹45,000 / month'
  }
};

export const initialResumeDoc: ResumeDocument = {
  id: 'res-doc-01',
  fileName: 'Aarav_Sharma_Resume_2026.pdf',
  fileSize: '242 KB',
  uploadedAt: '2026-10-15T10:30:00Z',
  lastParsedAt: '2026-10-15T10:31:12Z',
  extractedSkills: [
    { name: 'TypeScript', confirmed: true },
    { name: 'React', confirmed: true },
    { name: 'Node.js', confirmed: true },
    { name: 'PostgreSQL', confirmed: true },
    { name: 'Docker', confirmed: false },
    { name: 'Tailwind CSS', confirmed: true },
    { name: 'Python', confirmed: true },
    { name: 'Redis', confirmed: false }
  ],
  extractedExperienceCount: 1,
  extractedProjectsCount: 2,
  verifiedByStudent: true,
  attentionItems: [
    { id: 'att-1', message: 'Docker and Redis skills extracted from project bullets are not yet marked as verified.', severity: 'info' },
    { id: 'att-2', message: 'Graduation date listed as May 2027. Some 2026 immediate full-time roles require earlier availability.', severity: 'warning' }
  ]
};

export const initialJobs: Job[] = [
  {
    id: 'job-101',
    title: 'Software Engineer Intern (Frontend / Full Stack)',
    company: 'Vercel',
    logoText: '▲',
    logoBg: 'bg-navy-800 text-white',
    location: 'Bangalore (Hybrid)',
    workMode: 'Hybrid',
    type: 'Internship',
    stipendSalary: '₹85,000 / month',
    deadline: '2026-11-24',
    postedDate: '2026-11-04',
    domain: 'Developer Tools & Cloud',
    experienceLevel: 'Student / New Grad',
    department: 'Core Frontend Infrastructure',
    description: 'Join the team building modern developer infrastructure. You will work on real-world frontend web apps, developer dashboard workflows, and high-performance React component libraries.',
    responsibilities: [
      'Build responsive, highly accessible web interfaces in Next.js and TypeScript.',
      'Collaborate with product designers to implement pixel-perfect user experiences.',
      'Write comprehensive unit and integration tests for critical web workflows.',
      'Contribute to open source design system packages.'
    ],
    requirements: [
      'Strong command over modern TypeScript, React, and browser APIs.',
      'Familiarity with Tailwind CSS and responsive component architecture.',
      'Prior internship or notable open-source project contributions.',
      'Clean Git workflow and code review discipline.'
    ],
    requiredSkills: ['TypeScript', 'React', 'Tailwind CSS', 'REST APIs', 'Git & GitHub'],
    preferredSkills: ['Next.js', 'Node.js', 'Testing Library', 'Web Performance'],
    fitScore: 94,
    matchCategory: 'Strong match',
    matchingSkills: ['TypeScript', 'React', 'Tailwind CSS', 'Node.js', 'Git & GitHub', 'REST APIs'],
    missingSkills: ['Next.js', 'Testing Library'],
    matchExplanation: 'Exceptional match for your TypeScript and React background. Your Campus Peer Marketplace project demonstrated clean UI state management matching their design system needs.',
    saved: true
  },
  {
    id: 'job-102',
    title: 'Junior Software Engineer (Backend Systems)',
    company: 'Stripe',
    logoText: 'S',
    logoBg: 'bg-steel-600 text-white',
    location: 'Bangalore (On-site)',
    workMode: 'On-site',
    type: 'Full-time',
    stipendSalary: '₹22,00,000 - ₹26,00,000 / yr',
    deadline: '2026-11-20',
    postedDate: '2026-10-28',
    domain: 'Fintech & Global Payments',
    experienceLevel: '0 - 1 Years',
    department: 'Payment Processing Engine',
    description: 'Help build the financial infrastructure of the internet. Our team designs resilient, transactional backend services handling billions in commerce with five-nines availability.',
    responsibilities: [
      'Design and deploy scalable backend services in Node.js / Java / Go.',
      'Work with relational databases ensuring strict ACID transactional consistency.',
      'Partner with security and reliability engineers on latency-critical endpoints.'
    ],
    requirements: [
      'Solid foundations in Data Structures, Algorithms, and System Design fundamentals.',
      'Hands-on experience with SQL databases and distributed transactions.',
      'Knowledge of asynchronous processing and message queues.'
    ],
    requiredSkills: ['Data Structures & Algorithms', 'PostgreSQL', 'Node.js', 'REST APIs'],
    preferredSkills: ['Apache Kafka', 'Distributed Systems', 'Docker', 'Redis'],
    fitScore: 88,
    matchCategory: 'Strong match',
    matchingSkills: ['Data Structures & Algorithms', 'PostgreSQL', 'Node.js', 'REST APIs', 'Docker'],
    missingSkills: ['Apache Kafka', 'Distributed Systems at Scale'],
    matchExplanation: 'Strong alignment with your distributed task queue project and database optimization experience at InnovateCloud Labs. Interview is actively in progress!',
    saved: true
  },
  {
    id: 'job-103',
    title: 'Product Engineer Intern',
    company: 'Linear',
    logoText: 'L',
    logoBg: 'bg-navy-900 text-white',
    location: 'Remote (India)',
    workMode: 'Remote',
    type: 'Internship',
    stipendSalary: '₹95,000 / month',
    deadline: '2026-11-30',
    postedDate: '2026-11-02',
    domain: 'Productivity & Issue Tracking',
    experienceLevel: 'Student / New Grad',
    department: 'Client Applications',
    description: 'We build toolsets that high-performing software teams love using every day. Speed, keyboard-first navigation, and aesthetic restraint are core to our identity.',
    responsibilities: [
      'Craft sub-50ms interactive web client features in React & TypeScript.',
      'Optimize offline-first sync mechanics and client data persistence.',
      'Participate in daily product polish discussions and user feedback review.'
    ],
    requirements: [
      'Deep enthusiasm for UI craftsmanship and performance benchmarks.',
      'Fluency in modern TypeScript, React, and CSS layout engines.',
      'Demonstrated portfolio of personal web applications.'
    ],
    requiredSkills: ['TypeScript', 'React', 'Tailwind CSS', 'Git & GitHub'],
    preferredSkills: ['Client Sync Engines', 'WebSockets', 'Electron'],
    fitScore: 86,
    matchCategory: 'Strong match',
    matchingSkills: ['TypeScript', 'React', 'Tailwind CSS', 'Git & GitHub'],
    missingSkills: ['WebSockets', 'Client Sync Engines'],
    matchExplanation: 'Your UI polish and fast prototyping skills fit Linear’s ethos. Application material is currently ready for submission.',
    saved: true
  },
  {
    id: 'job-104',
    title: 'Platform Infrastructure Intern',
    company: 'Datadog',
    logoText: 'DD',
    logoBg: 'bg-status-warning text-white',
    location: 'Bangalore (Hybrid)',
    workMode: 'Hybrid',
    type: 'Internship',
    stipendSalary: '₹75,000 / month',
    deadline: '2026-12-05',
    postedDate: '2026-11-06',
    domain: 'Cloud Observability',
    experienceLevel: 'Student',
    department: 'Metrics Ingestion',
    description: 'Ingest trillions of data points across massive distributed infrastructure. Work on performance telemetry, data ingestion microservices, and cluster tooling.',
    responsibilities: [
      'Build telemetry intake proxies and data pipeline transformers.',
      'Profile memory and CPU bottlenecks across high-throughput services.',
      'Containerize test harnesses with Docker and Kubernetes.'
    ],
    requirements: [
      'Good understanding of OS concepts, networking, and concurrent computing.',
      'Comfort with backend languages (Python/Node.js/Go).',
      'Curiosity about metrics, logs, and distributed traces.'
    ],
    requiredSkills: ['Python', 'Docker', 'REST APIs', 'Data Structures & Algorithms'],
    preferredSkills: ['Kubernetes', 'Prometheus', 'Kafka', 'Go'],
    fitScore: 78,
    matchCategory: 'Good match',
    matchingSkills: ['Python', 'Docker', 'REST APIs', 'Data Structures & Algorithms'],
    missingSkills: ['Kubernetes', 'Prometheus', 'Kafka'],
    matchExplanation: 'Solid backend foundations. Adding basic Prometheus or telemetry pipeline notes to your resume will strengthen your application significantly.',
    saved: false
  },
  {
    id: 'job-105',
    title: 'Graduate Software Engineer',
    company: 'Atlassian',
    logoText: 'A',
    logoBg: 'bg-steel-700 text-white',
    location: 'Bangalore (Hybrid)',
    workMode: 'Hybrid',
    type: 'Full-time',
    stipendSalary: '₹19,00,000 / yr',
    deadline: '2026-11-18',
    postedDate: '2026-10-20',
    domain: 'Enterprise Collaboration',
    experienceLevel: 'New Graduate',
    department: 'Jira Core Platform',
    description: 'Help global teams plan, track, and ship world-class software. Work on enterprise-scale cloud microservices powering millions of engineering teams.',
    responsibilities: [
      'Write resilient microservice endpoints with high automated test coverage.',
      'Participate in architecture reviews and sprint planning.',
      'Collaborate across distributed engineering hubs in Sydney and Bangalore.'
    ],
    requirements: [
      'B.Tech / B.E in Computer Science or related degree with minimum 7.5 CGPA.',
      'Demonstrated expertise in Object Oriented Programming and Data Structures.',
      'Clean coding practices and problem-solving mindset.'
    ],
    requiredSkills: ['Data Structures & Algorithms', 'PostgreSQL', 'Node.js', 'Git & GitHub'],
    preferredSkills: ['Java / Spring Boot', 'AWS / Cloud', 'System Architecture'],
    fitScore: 82,
    matchCategory: 'Good match',
    matchingSkills: ['Data Structures & Algorithms', 'PostgreSQL', 'Node.js', 'Git & GitHub'],
    missingSkills: ['Java / Spring Boot', 'System Architecture'],
    matchExplanation: 'Matches your academic excellence (8.84 CGPA) and core CS foundations. Coding assessment is scheduled for this week.',
    saved: true
  },
  {
    id: 'job-106',
    title: 'Edge Systems Intern',
    company: 'Cloudflare',
    logoText: 'CF',
    logoBg: 'bg-status-warning text-white',
    location: 'Remote',
    workMode: 'Remote',
    type: 'Internship',
    stipendSalary: '₹90,000 / month',
    deadline: '2026-12-15',
    postedDate: '2026-11-08',
    domain: 'Networking & Edge Computing',
    experienceLevel: 'Student',
    department: 'Workers Runtime',
    description: 'Work at the intersection of edge computing and modern web protocols. Learn how JavaScript runtimes execute thousands of miles closer to end users.',
    responsibilities: [
      'Develop sample applications and benchmarks for V8 isolate runtime.',
      'Improve developer tooling and CLI documentation.',
      'Test network routing edge cases across diverse geographic regions.'
    ],
    requirements: [
      'Familiarity with HTTP/2, HTTP/3, DNS, and TLS networking concepts.',
      'Strong JavaScript / TypeScript proficiency.',
      'Eager curiosity for network systems.'
    ],
    requiredSkills: ['TypeScript', 'REST APIs', 'Git & GitHub'],
    preferredSkills: ['WebAssembly', 'Rust', 'DNS & Networking'],
    fitScore: 68,
    matchCategory: 'Partial match',
    matchingSkills: ['TypeScript', 'REST APIs', 'Git & GitHub'],
    missingSkills: ['Networking Protocols', 'WebAssembly', 'Rust'],
    matchExplanation: 'Good foundational TypeScript skills, but networking and low-level protocol knowledge are required for high competitiveness.',
    saved: false
  }
];

export const initialApplications: Application[] = [
  {
    id: 'app-001',
    jobId: 'job-102',
    jobTitle: 'Junior Software Engineer (Backend Systems)',
    company: 'Stripe',
    location: 'Bangalore (On-site)',
    jobType: 'Full-time',
    dateAdded: '2026-10-30',
    appliedDate: '2026-11-01',
    deadline: '2026-11-20',
    stage: 'Interview',
    nextAction: 'Round 2: Technical Deep Dive & Systems Architecture',
    nextActionDueDate: '2026-11-15',
    lastUpdated: '2026-11-08',
    notes: [
      'Cleared initial technical screening on Nov 4. Interviewer praised the Redis task runner explanation.',
      'Focus areas for Round 2: Relational database transaction isolation levels and concurrency control.'
    ],
    tailoredResumeId: 'res-draft-stripe',
    coverLetterId: 'cov-draft-stripe',
    timeline: [
      { id: 'tl-1', date: '2026-10-30', stage: 'Interested', note: 'Role saved from Nexora recommended feed.', author: 'Student' },
      { id: 'tl-2', date: '2026-10-31', stage: 'Ready to apply', note: 'Tailored resume and application reviewed and approved.', author: 'Student' },
      { id: 'tl-3', date: '2026-11-01', stage: 'Applied', note: 'Submitted via campus referral portal.', author: 'Student' },
      { id: 'tl-4', date: '2026-11-04', stage: 'Assessment', note: 'Passed online problem solving test (100% score).', author: 'System' },
      { id: 'tl-5', date: '2026-11-08', stage: 'Interview', note: 'Round 2 scheduled for Saturday, Nov 15 at 3:00 PM IST.', author: 'Nexora Assistant' }
    ],
    interviewDetails: {
      date: '2026-11-15',
      time: '15:00 - 16:15 IST',
      round: 'Round 2: Systems Architecture & Concurrency',
      interviewers: ['Priya Nair (Senior Staff Engineer)', 'Rohan Verma (Tech Lead)'],
      platform: 'Google Meet',
      notes: 'Prepare a 5-minute overview of the telemetry aggregation pipeline built at InnovateCloud Labs.'
    }
  },
  {
    id: 'app-002',
    jobId: 'job-105',
    jobTitle: 'Graduate Software Engineer',
    company: 'Atlassian',
    location: 'Bangalore (Hybrid)',
    jobType: 'Full-time',
    dateAdded: '2026-10-25',
    appliedDate: '2026-10-27',
    deadline: '2026-11-18',
    stage: 'Assessment',
    nextAction: 'Complete HackerRank Coding Challenge (90 mins)',
    nextActionDueDate: '2026-11-14',
    lastUpdated: '2026-11-07',
    notes: [
      'HackerRank link received. Topics: Graph algorithms, dynamic programming, and clean code principles.',
      'Practice medium graph problems in practice arena before opening link.'
    ],
    timeline: [
      { id: 'tl-21', date: '2026-10-25', stage: 'Interested', note: 'Saved role after seeing 82% fit score.', author: 'Student' },
      { id: 'tl-22', date: '2026-10-27', stage: 'Applied', note: 'Applied through college placement cell channel.', author: 'Student' },
      { id: 'tl-23', date: '2026-11-07', stage: 'Assessment', note: 'Invitation received for online coding round.', author: 'System' }
    ]
  },
  {
    id: 'app-003',
    jobId: 'job-101',
    jobTitle: 'Software Engineer Intern (Frontend / Full Stack)',
    company: 'Vercel',
    location: 'Bangalore (Hybrid)',
    jobType: 'Internship',
    dateAdded: '2026-11-05',
    deadline: '2026-11-24',
    stage: 'Awaiting approval',
    nextAction: 'Review and approve tailored resume draft in Approval Centre',
    nextActionDueDate: '2026-11-12',
    lastUpdated: '2026-11-09',
    notes: [
      'Tailored resume emphasizes TypeScript component architecture and campus marketplace web app.',
      'Ensure verified metrics match actual internship outcomes before approving.'
    ],
    tailoredResumeId: 'res-draft-vercel',
    timeline: [
      { id: 'tl-31', date: '2026-11-05', stage: 'Interested', note: 'Role saved with 94% fit score.', author: 'Student' },
      { id: 'tl-32', date: '2026-11-08', stage: 'Preparing', note: 'Opened Resume Studio to customize project bullets.', author: 'Student' },
      { id: 'tl-33', date: '2026-11-09', stage: 'Awaiting approval', note: 'Resume customization submitted to Approval Centre for final student review.', author: 'Nexora Assistant' }
    ]
  },
  {
    id: 'app-004',
    jobId: 'job-103',
    jobTitle: 'Product Engineer Intern',
    company: 'Linear',
    location: 'Remote (India)',
    jobType: 'Internship',
    dateAdded: '2026-11-03',
    deadline: '2026-11-30',
    stage: 'Ready to apply',
    nextAction: 'Submit application packet through official careers portal',
    nextActionDueDate: '2026-11-16',
    lastUpdated: '2026-11-07',
    notes: [
      'Resume approved. Cover letter focuses on keyboard navigation design and frontend responsiveness.',
      'Portfolio link is verified and active.'
    ],
    tailoredResumeId: 'res-draft-linear',
    timeline: [
      { id: 'tl-41', date: '2026-11-03', stage: 'Interested', note: 'Added to target opportunities list.', author: 'Student' },
      { id: 'tl-42', date: '2026-11-06', stage: 'Awaiting approval', note: 'Drafted tailored documents.', author: 'Nexora Assistant' },
      { id: 'tl-43', date: '2026-11-07', stage: 'Ready to apply', note: 'Student explicitly approved resume & cover letter packet.', author: 'Student' }
    ]
  },
  {
    id: 'app-005',
    jobId: 'job-104',
    jobTitle: 'Platform Infrastructure Intern',
    company: 'Datadog',
    location: 'Bangalore (Hybrid)',
    jobType: 'Internship',
    dateAdded: '2026-11-07',
    deadline: '2026-12-05',
    stage: 'Preparing',
    nextAction: 'Draft tailored cover letter focusing on telemetry systems experience',
    nextActionDueDate: '2026-11-18',
    lastUpdated: '2026-11-08',
    notes: [
      'Review missing skills (Kafka/Prometheus) in Skill Roadmap before finalizing materials.'
    ],
    timeline: [
      { id: 'tl-51', date: '2026-11-07', stage: 'Interested', note: 'Saved role from discovery list.', author: 'Student' },
      { id: 'tl-52', date: '2026-11-08', stage: 'Preparing', note: 'Started tailoring application packet.', author: 'Student' }
    ]
  },
  {
    id: 'app-006',
    jobId: 'job-106',
    jobTitle: 'Edge Systems Intern',
    company: 'Cloudflare',
    location: 'Remote',
    jobType: 'Internship',
    dateAdded: '2026-11-08',
    appliedDate: '2026-11-09',
    deadline: '2026-12-15',
    stage: 'Applied',
    nextAction: 'Monitor student portal for initial response',
    nextActionDueDate: '2026-11-23',
    lastUpdated: '2026-11-09',
    notes: [
      'Submitted standard technical resume. Follow-up reminder scheduled for 14 days post-application.'
    ],
    timeline: [
      { id: 'tl-61', date: '2026-11-08', stage: 'Interested', note: 'Discovered role.', author: 'Student' },
      { id: 'tl-62', date: '2026-11-09', stage: 'Applied', note: 'Submitted application on Cloudflare Greenhouse portal.', author: 'Student' }
    ]
  }
];

export const initialResumeDrafts: Record<string, ResumeDraft> = {
  'res-draft-vercel': {
    id: 'res-draft-vercel',
    jobId: 'job-101',
    jobTitle: 'Software Engineer Intern (Frontend / Full Stack)',
    company: 'Vercel',
    createdAt: '2026-11-08T14:00:00Z',
    updatedAt: '2026-11-09T18:20:00Z',
    summary: 'Final-year Computer Science undergraduate with proven experience building fast, accessible web applications using TypeScript and React. Experienced in optimizing client-side rendering, crafting reusable design systems, and deploying resilient full-stack applications.',
    originalSummary: 'Computer Science undergraduate looking for software engineering roles in frontend and full stack development.',
    skills: [
      { name: 'TypeScript', isHighlighted: true },
      { name: 'React', isHighlighted: true },
      { name: 'Tailwind CSS', isHighlighted: true },
      { name: 'Node.js', isHighlighted: false },
      { name: 'REST APIs', isHighlighted: true },
      { name: 'PostgreSQL', isHighlighted: false },
      { name: 'Git & GitHub', isHighlighted: true },
      { name: 'Docker', isHighlighted: false }
    ],
    experienceHighlights: [
      {
        id: 'eh-1',
        company: 'InnovateCloud Labs',
        role: 'Software Engineering Intern',
        bullet: 'Architected telemetry dashboard frontend components with zero layout shift, decreasing end-user load times by 38%.',
        originalBullet: 'Built telemetry aggregation pipeline processing 250k daily events using Node.js and Redis cache.',
        hasSuggestion: true,
        suggestion: 'Emphasize the frontend latency improvements and responsive component design relevant to Vercel’s core focus.',
        status: 'pending'
      },
      {
        id: 'eh-2',
        company: 'InnovateCloud Labs',
        role: 'Software Engineering Intern',
        bullet: 'Authored 14 automated integration and visual regression test suites for key customer navigation flows.',
        originalBullet: 'Authored 14 end-to-end integration test suites ensuring zero regression during major API v2 rollout.',
        hasSuggestion: false,
        status: 'accepted'
      }
    ],
    projectHighlights: [
      {
        id: 'ph-1',
        projectTitle: 'Campus Peer Marketplace',
        bullet: 'Constructed accessible, mobile-first design system utilizing Tailwind CSS and modular UI components supporting 1,400+ campus users.',
        originalBullet: 'Designed accessible responsive UI with shadcn/ui and optimized client-side search indexing.',
        hasSuggestion: true,
        suggestion: 'Highlight component accessibility (a11y) and design-system discipline.',
        status: 'pending'
      },
      {
        id: 'ph-2',
        projectTitle: 'Resilient Distributed Task Runner',
        bullet: 'Engineered real-time dashboard UI using Server-Sent Events (SSE) and reactive state hooks to visualize 1,000+ task executions.',
        originalBullet: 'Integrated live status dashboard using Server-Sent Events (SSE) supporting 1,000+ concurrent workers.',
        hasSuggestion: false,
        status: 'accepted'
      }
    ],
    approvalStatus: 'pending_approval'
  }
};

export const initialCoverLetters: Record<string, CoverLetterDraft> = {
  'cov-draft-linear': {
    id: 'cov-draft-linear',
    jobId: 'job-103',
    jobTitle: 'Product Engineer Intern',
    company: 'Linear',
    recipientName: 'Hiring Team',
    recipientTitle: 'Head of Engineering',
    recipientCompany: 'Linear Orbit Inc.',
    date: 'November 7, 2026',
    opening: 'Dear Linear Engineering Team,',
    bodyParagraph1: 'I am writing to express my strong enthusiasm for the Product Engineer Intern role at Linear. Having followed your engineering principles around keyboard-first workflows, micro-interactions, and sub-50ms responsiveness, I deeply respect your refusal to compromise on design discipline.',
    bodyParagraph2: 'During my internship at InnovateCloud Labs and through building open-source developer tooling like my Distributed Task Runner, I focused heavily on asynchronous state management and clean UI architecture. My background in TypeScript and React has trained me to prioritize zero-friction user experiences, strict type boundaries, and lightweight frontend bundles.',
    closing: 'I would welcome the opportunity to bring my attention to detail and hunger for craft to Linear this upcoming term. Thank you for your time and consideration.',
    wordCount: 168,
    approvalStatus: 'approved'
  },
  'cov-draft-datadog': {
    id: 'cov-draft-datadog',
    jobId: 'job-104',
    jobTitle: 'Platform Infrastructure Intern',
    company: 'Datadog',
    recipientName: 'University Recruiting Team',
    recipientTitle: 'Campus Talent Partner',
    recipientCompany: 'Datadog India',
    date: 'November 9, 2026',
    opening: 'Dear Datadog Recruiting Team,',
    bodyParagraph1: 'I am excited to apply for the Platform Infrastructure Intern position. As a final-year Computer Science student passionate about distributed systems and performance telemetry, Datadog’s work in real-time observability at planetary scale represents the exact engineering challenge I want to tackle.',
    bodyParagraph2: 'In my previous internship, I designed an event aggregation pipeline handling 250k daily telemetry records and redesigned PostgreSQL indexes to cut query latencies by 38%. My hands-on projects with Redis message queues and containerized test suites have given me practical exposure to asynchronous data streaming and reliability engineering.',
    closing: 'I look forward to discussing how my systems curiosity and backend foundations can support Datadog’s metrics ingestion team.',
    wordCount: 154,
    approvalStatus: 'draft'
  }
};

export const initialApprovals: ApprovalItem[] = [
  {
    id: 'appr-01',
    type: 'tailored_resume',
    title: 'Tailored Resume for Vercel',
    jobId: 'job-101',
    jobTitle: 'Software Engineer Intern (Frontend / Full Stack)',
    company: 'Vercel',
    createdAt: '2026-11-09T18:20:00Z',
    status: 'pending',
    summary: 'Customized summary and bullet points focusing on frontend performance, responsive UI design systems, and real-time dashboard visualization.',
    changesCount: 3,
    unverifiedWarnings: [
      'Verify that the 38% latency reduction at InnovateCloud Labs specifically involved the frontend dashboard telemetry.'
    ],
    contentPreview: {
      beforeText: 'Built telemetry aggregation pipeline processing 250k daily events using Node.js and Redis cache.',
      afterText: 'Architected telemetry dashboard frontend components with zero layout shift, decreasing end-user load times by 38%.',
      highlights: ['TypeScript', 'Design Systems', 'Performance benchmark']
    }
  },
  {
    id: 'appr-02',
    type: 'cover_letter',
    title: 'Cover Letter for Datadog Platform Intern',
    jobId: 'job-104',
    jobTitle: 'Platform Infrastructure Intern',
    company: 'Datadog',
    createdAt: '2026-11-09T19:00:00Z',
    status: 'pending',
    summary: 'Concise 154-word cover letter highlighting event aggregation experience and database latency optimization.',
    changesCount: 2,
    unverifiedWarnings: [],
    contentPreview: {
      afterText: 'In my previous internship, I designed an event aggregation pipeline handling 250k daily telemetry records and redesigned PostgreSQL indexes...',
      highlights: ['Distributed Systems', 'PostgreSQL', 'Redis Queue']
    }
  },
  {
    id: 'appr-03',
    type: 'follow_up',
    title: 'Post-Round 1 Confirmation for Stripe',
    jobId: 'job-102',
    jobTitle: 'Junior Software Engineer (Backend Systems)',
    company: 'Stripe',
    createdAt: '2026-11-08T16:00:00Z',
    status: 'pending',
    summary: 'Professional acknowledgement and preparation confirmation for Round 2 Technical Deep Dive with Priya Nair and Rohan Verma.',
    changesCount: 1,
    unverifiedWarnings: [],
    contentPreview: {
      afterText: 'Subject: Confirmation & Preparation: Round 2 Systems Interview (Aarav Sharma)\n\nDear Priya and Rohan, Thank you for scheduling the Round 2 interview on Nov 15...',
      highlights: ['Interview Confirmation', 'Systems Prep']
    }
  }
];

export const initialCalendarEvents: CalendarEvent[] = [
  {
    id: 'cal-1',
    title: 'Stripe — Round 2 Systems Architecture Interview',
    type: 'interview',
    date: '2026-11-15',
    time: '15:00 - 16:15 IST',
    applicationId: 'app-001',
    company: 'Stripe',
    description: 'Technical deep dive with Priya Nair and Rohan Verma. Topics: Distributed transactions and Redis task runner.',
    priority: 'high',
    completed: false
  },
  {
    id: 'cal-2',
    title: 'Atlassian — HackerRank Coding Challenge Deadline',
    type: 'assessment',
    date: '2026-11-14',
    time: '23:59 IST',
    applicationId: 'app-002',
    company: 'Atlassian',
    description: '90-minute timed test. Covers Graph algorithms and OOP design.',
    priority: 'high',
    completed: false
  },
  {
    id: 'cal-3',
    title: 'Vercel — Application Deadline for Winter Intern Batch',
    type: 'deadline',
    date: '2026-11-24',
    time: '23:59 IST',
    applicationId: 'app-003',
    company: 'Vercel',
    description: 'Final submission deadline for frontend infrastructure internship.',
    priority: 'medium',
    completed: false
  },
  {
    id: 'cal-4',
    title: 'Review and Approve Tailored Resume for Vercel',
    type: 'personal',
    date: '2026-11-12',
    time: '11:00 IST',
    applicationId: 'app-003',
    company: 'Vercel',
    description: 'Check highlighted bullet points in Approval Centre before portal submission.',
    priority: 'medium',
    completed: false
  },
  {
    id: 'cal-5',
    title: 'Linear — Target Application Submission',
    type: 'deadline',
    date: '2026-11-16',
    time: '18:00 IST',
    applicationId: 'app-004',
    company: 'Linear',
    description: 'Packet is ready and approved. Submit through careers portal.',
    priority: 'medium',
    completed: false
  },
  {
    id: 'cal-6',
    title: 'Practice Session: Database Concurrency & Isolation',
    type: 'prep',
    date: '2026-11-13',
    time: '17:00 IST',
    description: 'Self-guided practice in Nexora Interview Prep for upcoming Stripe round.',
    priority: 'high',
    completed: false
  }
];

export const initialInterviewSessions: InterviewSession[] = [
  {
    id: 'session-tech-01',
    role: 'Software Engineer (Backend Systems)',
    company: 'Stripe',
    type: 'Technical',
    difficulty: 'Mid',
    startedAt: '2026-11-06T14:30:00Z',
    completedAt: '2026-11-06T15:10:00Z',
    status: 'completed',
    currentQuestionIndex: 3,
    questions: [
      {
        id: 'q-1',
        question: 'Explain how you would design an idempotent payment processing endpoint to prevent duplicate charges when a client retries.',
        category: 'System Design',
        hint: 'Think about idempotency keys, database transaction boundaries, and token lifecycles.',
        contextWhyAsked: 'Critical for payment systems reliability when clients suffer network dropouts.',
        sampleFramework: 'Define idempotency key header -> Check cache/DB for key -> If found, return cached response -> If new, acquire lock & process in single transaction.',
        studentAnswer: 'Clients send an Idempotency-Key UUID header. We first check an in-memory Redis lock. If not seen, insert a pending record in PostgreSQL with a unique constraint on the key. Once payment succeeds, we store the full result and return. Subsequent duplicate requests find the stored response and return immediately without re-triggering bank transfers.'
      },
      {
        id: 'q-2',
        question: 'What happens when two concurrent database transactions attempt to update the same user wallet balance simultaneously? How do you prevent lost updates?',
        category: 'Technical',
        hint: 'Compare optimistic locking with version columns versus pessimistic row locks (SELECT FOR UPDATE).',
        contextWhyAsked: 'Evaluates real understanding of ACID properties and concurrency control under load.',
        sampleFramework: 'Pessimistic: SELECT ... FOR UPDATE blocks others. Optimistic: UPDATE WHERE id = x AND version = v. Compare trade-offs for high contention.',
        studentAnswer: 'In high-concurrency wallet scenarios, naive Read-Modify-Write creates race conditions where the second transaction overwrites the first. We can use pessimistic locking with SELECT balance FROM wallets WHERE user_id = $1 FOR UPDATE, ensuring other writers block until commit. Alternatively, atomic SQL like UPDATE wallets SET balance = balance + :amount WHERE balance + :amount >= 0 prevents race conditions cleanly.'
      },
      {
        id: 'q-3',
        question: 'In your distributed task runner project, how did you handle task worker crashes midway through execution?',
        category: 'Technical',
        hint: 'Explain heartbeat monitors, visibility timeouts, and dead-letter queues.',
        contextWhyAsked: 'Checks candidate’s personal knowledge of edge cases in their claimed projects.',
        sampleFramework: 'Task leased with visibility timeout -> Worker periodically sends heartbeat -> If heartbeat expires before ACK, orchestrator reassigns task to pool.',
        studentAnswer: 'Tasks were moved to a "Processing" state with an associated Redis lease timestamp (visibility timeout of 30s). Workers sent heartbeats every 10s. If a worker crashed, a scavenger job discovered expired leases and requeued the task with an incremented attempt counter. After 3 failures, the task was sent to a dead-letter queue for inspection.'
      }
    ]
  }
];

export const initialFeedbackReport: FeedbackReport = {
  id: 'rep-01',
  sessionId: 'session-tech-01',
  role: 'Software Engineer (Backend Systems)',
  company: 'Stripe',
  interviewType: 'Technical Systems Practice',
  completedDate: '2026-11-06',
  overallScore: 84,
  scores: {
    communication: 88,
    technical: 86,
    relevance: 90,
    clarity: 82,
    delivery: 74
  },
  overallAssessment: 'Strong performance on systems architecture and transaction integrity. Your explanation of idempotency and database locks was clear, practical, and grounded in real-world trade-offs.',
  strongPoints: [
    'Demonstrated clear understanding of idempotency keys with database unique constraints.',
    'Crisp explanation of atomic SQL updates and pessimistic row locking under race conditions.',
    'Directly connected theoretical concepts to concrete project implementations (Redis lease timeouts).'
  ],
  areasToImprove: [
    'Elaborate on edge cases: what happens when Redis crashes before the DB record is persisted?',
    'Clarify recovery mechanisms for long-running batch transactions vs latency-critical single transactions.',
    'Speak with slightly more structured cadence when outlining sequential steps (use "First, Next, Finally").'
  ],
  recommendedNextPractice: 'Practice deep dive on Distributed Locks (Redlock algorithm) and Kafka partition offset management.',
  questionFeedback: [
    {
      questionId: 'q-1',
      questionText: 'Explain how you would design an idempotent payment processing endpoint.',
      studentAnswer: 'Clients send an Idempotency-Key UUID header. We first check an in-memory Redis lock...',
      score: 88,
      critique: 'Very solid approach combining Redis cache lookup with PostgreSQL unique constraints.',
      improvedApproach: 'Mention how long the idempotency key should be retained (e.g. 24-48 hours TTL in Redis).'
    },
    {
      questionId: 'q-2',
      questionText: 'What happens when two concurrent database transactions attempt to update balance simultaneously?',
      studentAnswer: 'In high-concurrency wallet scenarios, naive Read-Modify-Write creates race conditions...',
      score: 85,
      critique: 'Understood both pessimistic locking and atomic SQL statements.',
      improvedApproach: 'Highlight database isolation levels (Read Committed vs Serializable) and lock timeout configurations.'
    },
    {
      questionId: 'q-3',
      questionText: 'In your distributed task runner project, how did you handle task worker crashes?',
      studentAnswer: 'Tasks were moved to a "Processing" state with an associated Redis lease timestamp...',
      score: 80,
      critique: 'Clear explanation of visibility timeouts and dead-letter queues.',
      improvedApproach: 'Briefly note poison pills (tasks that cause the worker process itself to crash every time).'
    }
  ]
};

export const initialRoadmapTasks: RoadmapTask[] = [
  {
    id: 'task-rm-1',
    skillName: 'Event Streaming & Kafka Fundamentals',
    category: 'Backend',
    priority: 'High',
    estimatedHours: 8,
    status: 'In progress',
    reason: 'Identified as missing skill in Stripe and Datadog backend role requirements. Essential for distributed event handling.',
    targetRoles: ['Backend Engineer', 'Platform Infrastructure Intern'],
    resources: [
      { title: 'Apache Kafka Architecture Core Concepts', type: 'Doc', link: 'https://kafka.apache.org/documentation' },
      { title: 'Build a Node.js Consumer/Producer with KafkaJS', type: 'Project', link: 'https://github.com/tulios/kafkajs' }
    ],
    relatedJobCount: 3
  },
  {
    id: 'task-rm-2',
    skillName: 'PostgreSQL Indexing & Query Profiling',
    category: 'Database',
    priority: 'High',
    estimatedHours: 6,
    status: 'In progress',
    reason: 'Directly tested in Stripe Round 2 interview. Build deep confidence in EXPLAIN ANALYZE and B-Tree vs GIN indexing.',
    targetRoles: ['Backend Engineer', 'Full Stack Developer'],
    resources: [
      { title: 'Use The Index, Luke! - Guide to Database Performance', type: 'Doc', link: 'https://use-the-index-luke.com' },
      { title: 'Benchmarking Query Execution Plans', type: 'Exercise', link: 'https://explain.depesz.com' }
    ],
    relatedJobCount: 4
  },
  {
    id: 'task-rm-3',
    skillName: 'Container Orchestration with Docker & Kubernetes Basics',
    category: 'Systems',
    priority: 'Recommended',
    estimatedHours: 10,
    status: 'Not started',
    reason: 'Required for Datadog Platform Intern and Cloud infrastructure positions.',
    targetRoles: ['Platform Infrastructure Intern'],
    resources: [
      { title: 'Kubernetes Up & Running - Pods and Deployments', type: 'Doc', link: 'https://kubernetes.io/docs/tutorials/' },
      { title: 'Containerize Multi-service App with Docker Compose', type: 'Project', link: 'https://docs.docker.com/compose/' }
    ],
    relatedJobCount: 2
  },
  {
    id: 'task-rm-4',
    skillName: 'Frontend Testing with React Testing Library',
    category: 'Frontend',
    priority: 'Recommended',
    estimatedHours: 5,
    status: 'Completed',
    reason: 'Required for Vercel and Linear frontend engineering roles.',
    targetRoles: ['Frontend Engineer', 'Product Engineer Intern'],
    resources: [
      { title: 'Testing Implementation Details vs User Actions', type: 'Doc', link: 'https://testing-library.com/docs/react-testing-library/intro/' }
    ],
    relatedJobCount: 3
  },
  {
    id: 'task-rm-5',
    skillName: 'Behavioral Interview STAR Technique',
    category: 'Behavioral',
    priority: 'Optional',
    estimatedHours: 3,
    status: 'In progress',
    reason: 'Standard expectation in all final round interviews (Atlassian values round & Stripe leadership principles).',
    targetRoles: ['All Opportunities'],
    resources: [
      { title: 'Structuring Leadership & Conflict Examples', type: 'Exercise', link: 'https://www.themuse.com/advice/star-interview-method' }
    ],
    relatedJobCount: 6
  }
];

export const initialFollowUps: FollowUpItem[] = [
  {
    id: 'fu-01',
    applicationId: 'app-001',
    company: 'Stripe',
    role: 'Junior Software Engineer (Backend Systems)',
    recipientName: 'Priya Nair & Rohan Verma',
    recipientEmail: 'recruiting-in@stripe.com',
    triggerReason: 'Upcoming Round 2 interview in 5 days',
    suggestedDate: '2026-11-10',
    status: 'awaiting_approval',
    subject: 'Confirmation & Preparation Overview — Round 2 Interview (Aarav Sharma)',
    message: 'Dear Priya and Rohan,\n\nThank you for scheduling the Round 2 Systems Architecture session for Saturday, Nov 15. I have reviewed the telemetry architecture from my internship at InnovateCloud Labs and look forward to discussing database concurrency and transaction isolation.\n\nPlease let me know if any additional code samples would be helpful ahead of time.\n\nBest regards,\nAarav Sharma'
  },
  {
    id: 'fu-02',
    applicationId: 'app-006',
    company: 'Cloudflare',
    role: 'Edge Systems Intern',
    recipientName: 'University Recruiting',
    recipientEmail: 'careers@cloudflare.com',
    triggerReason: 'Follow-up 10 days after application submission',
    suggestedDate: '2026-11-19',
    status: 'draft',
    subject: 'Application Status Follow-up: Edge Systems Intern (Aarav Sharma)',
    message: 'Dear Cloudflare Recruiting Team,\n\nI hope your week is going well. I recently submitted my application for the Edge Systems Intern role (Job ID: #CF-9812). I remain enthusiastic about Cloudflare’s Workers platform and would welcome the chance to share my background in distributed systems and TypeScript.\n\nThank you for your time and guidance.\n\nSincerely,\nAarav Sharma'
  }
];

export const initialAssistantMessages: AssistantChatMessage[] = [
  {
    id: 'msg-1',
    sender: 'assistant',
    timestamp: '10:00 AM',
    content: 'Good morning, Aarav! Here is where your placement journey stands today:\n\n• **Stripe Round 2** is in 5 days (Nov 15). Focus on PostgreSQL locks and transaction isolation.\n• **Vercel tailored resume** is waiting for your review in the Approval Centre.\n• **Atlassian coding challenge** deadline is Nov 14.\n\nHow would you like to proceed today?',
    quickReplies: [
      'Review Vercel resume draft',
      'Prep for Stripe Round 2',
      'Explain my missing skills for Datadog'
    ]
  }
];
