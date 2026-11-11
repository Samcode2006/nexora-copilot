import { createContext, useContext } from 'react';
import type { Profile as BackendProfile } from '../lib/api';
import type {
  StudentProfile,
  Job,
  Application,
  ApplicationStage,
  ResumeDocument,
  ResumeDraft,
  CoverLetterDraft,
  ApprovalItem,
  CalendarEvent,
  InterviewSession,
  FeedbackReport,
  RoadmapTask,
  FollowUpItem,
  AssistantChatMessage,
} from '../types';

export interface AppContextType {
  // Profile
  profile: StudentProfile;
  updateProfile: (updated: Partial<StudentProfile>) => void;

  // Resume Document
  resumeDoc: ResumeDocument;
  uploadResume: (file: { name: string; size: string }) => void;
  verifySkill: (skillName: string) => void;

  // Jobs
  jobs: Job[];
  toggleSaveJob: (jobId: string) => void;
  getJobById: (jobId: string) => Job | undefined;

  // Applications
  applications: Application[];
  updateApplicationStage: (applicationId: string, stage: ApplicationStage, note?: string) => void;
  createApplication: (jobId: string) => Application;
  getApplicationById: (applicationId: string) => Application | undefined;

  // Resume Studio
  resumeDrafts: Record<string, ResumeDraft>;
  saveResumeDraft: (draft: ResumeDraft) => void;
  updateBulletStatus: (jobId: string, type: 'experience' | 'project', id: string, status: 'accepted' | 'rejected') => void;
  submitResumeForApproval: (draft: ResumeDraft) => void;

  // Cover Letters
  coverLetters: Record<string, CoverLetterDraft>;
  saveCoverLetter: (letter: CoverLetterDraft) => void;
  submitCoverLetterForApproval: (letter: CoverLetterDraft) => void;

  // Approvals
  approvals: ApprovalItem[];
  approveItem: (approvalId: string) => void;
  rejectItem: (approvalId: string) => void;

  // Calendar & Reminders
  calendarEvents: CalendarEvent[];
  addCalendarEvent: (event: Omit<CalendarEvent, 'id'>) => void;
  toggleEventCompletion: (eventId: string) => void;

  // Interview Prep
  interviewSessions: InterviewSession[];
  activeSession: InterviewSession | null;
  startNewSession: (role: string, company: string, type: 'Technical' | 'Behavioural' | 'HR' | 'Role-specific', difficulty: 'Junior' | 'Mid' | 'Challenging') => string;
  submitAnswer: (sessionId: string, questionIndex: number, answer: string) => void;
  completeSession: (sessionId: string) => void;

  // Feedback
  feedbackReport: FeedbackReport;

  // Skill Roadmap
  roadmapTasks: RoadmapTask[];
  updateTaskStatus: (taskId: string, status: 'Not started' | 'In progress' | 'Completed') => void;
  addRoadmapTask: (task: Omit<RoadmapTask, 'id' | 'status' | 'relatedJobCount'>) => void;

  // Follow-ups
  followUps: FollowUpItem[];
  saveFollowUpDraft: (followUp: FollowUpItem) => void;
  requestFollowUpApproval: (followUpId: string) => void;

  // Assistant
  assistantMessages: AssistantChatMessage[];
  sendMessageToAssistant: (text: string) => void;

  // Global Reset for testing
  resetDemoData: () => void;

  // FastAPI Backend Profile Sync
  backendProfile: BackendProfile | null;
  backendProfileLoading: boolean;
  backendProfileError: string | null;
  refreshBackendProfile: () => Promise<void>;
}

export const AppContext = createContext<AppContextType | undefined>(undefined);

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

