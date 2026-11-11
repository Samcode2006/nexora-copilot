export type JobWorkMode = 'Remote' | 'Hybrid' | 'On-site';
export type JobType = 'Internship' | 'Full-time' | 'Co-op';
export type MatchCategory = 'Strong match' | 'Good match' | 'Partial match' | 'Low match';

export interface SkillItem {
  id: string;
  name: string;
  category: 'frontend' | 'backend' | 'data' | 'tools' | 'core';
  level: 'Beginner' | 'Intermediate' | 'Advanced';
  verified: boolean;
}

export interface ProjectItem {
  id: string;
  title: string;
  description: string;
  technologies: string[];
  role: string;
  highlights: string[];
  link?: string;
  github?: string;
}

export interface ExperienceItem {
  id: string;
  role: string;
  company: string;
  location: string;
  startDate: string;
  endDate: string;
  current: boolean;
  description: string;
  highlights: string[];
}

export interface EducationItem {
  id: string;
  institution: string;
  degree: string;
  field: string;
  startYear: string;
  endYear: string;
  grade: string;
}

export interface CertificationItem {
  id: string;
  title: string;
  issuer: string;
  issueDate: string;
  credentialUrl?: string;
}

export interface CareerPreferences {
  targetRoles: string[];
  preferredDomains: string[];
  preferredLocations: string[];
  employmentType: 'Internship' | 'Full-time' | 'Both';
  workMode: 'Remote' | 'Hybrid' | 'On-site' | 'Any';
  skillsOfInterest: string[];
  companyTypes: string[];
  minStipendSalary: string;
}

export interface StudentProfile {
  id: string;
  fullName: string;
  email: string;
  phone: string;
  college: string;
  degree: string;
  branch: string;
  graduationYear: string;
  currentYear: string;
  location: string;
  bio: string;
  avatarUrl?: string;
  completeness: number; // 0-100
  links: {
    github: string;
    linkedin: string;
    portfolio: string;
  };
  skills: SkillItem[];
  education: EducationItem[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  certifications: CertificationItem[];
  preferences: CareerPreferences;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  logoText: string;
  logoBg: string;
  location: string;
  workMode: JobWorkMode;
  type: JobType;
  stipendSalary: string;
  deadline: string;
  postedDate: string;
  domain: string;
  experienceLevel: string;
  description: string;
  responsibilities: string[];
  requirements: string[];
  requiredSkills: string[];
  preferredSkills: string[];
  fitScore: number;
  matchCategory: MatchCategory;
  matchingSkills: string[];
  missingSkills: string[];
  matchExplanation: string;
  saved: boolean;
  department: string;
}

export type ApplicationStage = 
  | 'Interested'
  | 'Preparing'
  | 'Awaiting approval'
  | 'Ready to apply'
  | 'Applied'
  | 'Assessment'
  | 'Interview'
  | 'Offer'
  | 'Rejected'
  | 'Withdrawn';

export interface ApplicationTimelineEvent {
  id: string;
  date: string;
  stage: ApplicationStage;
  note: string;
  author: 'Student' | 'System' | 'Nexora Assistant';
}

export interface Application {
  id: string;
  jobId: string;
  jobTitle: string;
  company: string;
  location: string;
  jobType: JobType;
  dateAdded: string;
  appliedDate?: string;
  deadline: string;
  stage: ApplicationStage;
  nextAction: string;
  nextActionDueDate: string;
  lastUpdated: string;
  notes: string[];
  tailoredResumeId?: string;
  coverLetterId?: string;
  timeline: ApplicationTimelineEvent[];
  interviewDetails?: {
    date: string;
    time: string;
    round: string;
    interviewers: string[];
    platform: string;
    notes: string;
  };
}

export interface ResumeDocument {
  id: string;
  fileName: string;
  fileSize: string;
  uploadedAt: string;
  lastParsedAt: string;
  extractedSkills: { name: string; confirmed: boolean }[];
  extractedExperienceCount: number;
  extractedProjectsCount: number;
  verifiedByStudent: boolean;
  attentionItems: { id: string; message: string; severity: 'warning' | 'info' }[];
}

export interface ResumeDraft {
  id: string;
  jobId: string;
  jobTitle: string;
  company: string;
  createdAt: string;
  updatedAt: string;
  summary: string;
  originalSummary: string;
  skills: { name: string; isHighlighted: boolean }[];
  experienceHighlights: {
    id: string;
    company: string;
    role: string;
    bullet: string;
    originalBullet: string;
    hasSuggestion: boolean;
    suggestion?: string;
    status: 'pending' | 'accepted' | 'rejected';
  }[];
  projectHighlights: {
    id: string;
    projectTitle: string;
    bullet: string;
    originalBullet: string;
    hasSuggestion: boolean;
    suggestion?: string;
    status: 'pending' | 'accepted' | 'rejected';
  }[];
  approvalStatus: 'draft' | 'pending_approval' | 'approved';
}

export interface CoverLetterDraft {
  id: string;
  jobId: string;
  jobTitle: string;
  company: string;
  recipientName: string;
  recipientTitle: string;
  recipientCompany: string;
  date: string;
  opening: string;
  bodyParagraph1: string;
  bodyParagraph2: string;
  closing: string;
  wordCount: number;
  approvalStatus: 'draft' | 'pending_approval' | 'approved';
}

export interface ApprovalItem {
  id: string;
  type: 'tailored_resume' | 'cover_letter' | 'follow_up';
  title: string;
  jobId: string;
  jobTitle: string;
  company: string;
  createdAt: string;
  status: 'pending' | 'approved' | 'rejected';
  summary: string;
  changesCount: number;
  unverifiedWarnings: string[];
  contentPreview: {
    beforeText?: string;
    afterText: string;
    highlights: string[];
  };
}

export interface CalendarEvent {
  id: string;
  title: string;
  type: 'deadline' | 'interview' | 'assessment' | 'follow_up' | 'prep' | 'personal';
  date: string; // YYYY-MM-DD
  time?: string;
  applicationId?: string;
  company?: string;
  description?: string;
  priority: 'low' | 'medium' | 'high';
  completed: boolean;
}

export interface InterviewQuestion {
  id: string;
  question: string;
  category: 'Technical' | 'Behavioural' | 'System Design' | 'HR';
  hint: string;
  contextWhyAsked: string;
  sampleFramework: string;
  studentAnswer?: string;
}

export interface InterviewSession {
  id: string;
  role: string;
  company: string;
  type: 'Technical' | 'Behavioural' | 'HR' | 'Role-specific';
  difficulty: 'Junior' | 'Mid' | 'Challenging';
  questions: InterviewQuestion[];
  currentQuestionIndex: number;
  startedAt: string;
  completedAt?: string;
  status: 'in_progress' | 'completed';
}

export interface FeedbackReport {
  id: string;
  sessionId: string;
  role: string;
  company: string;
  interviewType: string;
  completedDate: string;
  overallScore: number;
  scores: {
    communication: number;
    technical: number;
    relevance: number;
    clarity: number;
    delivery: number;
  };
  overallAssessment: string;
  strongPoints: string[];
  areasToImprove: string[];
  recommendedNextPractice: string;
  questionFeedback: {
    questionId: string;
    questionText: string;
    studentAnswer: string;
    score: number;
    critique: string;
    improvedApproach: string;
  }[];
}

export interface RoadmapTask {
  id: string;
  skillName: string;
  category: 'Frontend' | 'Backend' | 'Database' | 'Systems' | 'Behavioral';
  priority: 'High' | 'Recommended' | 'Optional';
  estimatedHours: number;
  status: 'Not started' | 'In progress' | 'Completed';
  reason: string;
  targetRoles: string[];
  resources: { title: string; type: 'Doc' | 'Project' | 'Exercise'; link: string }[];
  relatedJobCount: number;
}

export interface FollowUpItem {
  id: string;
  applicationId: string;
  company: string;
  role: string;
  recipientName: string;
  recipientEmail: string;
  triggerReason: string;
  suggestedDate: string;
  status: 'draft' | 'awaiting_approval' | 'approved' | 'sent';
  subject: string;
  message: string;
  sentDate?: string;
}

export interface AssistantChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  content: string;
  quickReplies?: string[];
  actionLink?: {
    label: string;
    to: string;
  };
}
