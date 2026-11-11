import React, { useState, useEffect, useCallback, useMemo, type ReactNode } from 'react';
import { useAuth } from '../auth/AuthContext';
import { ApiError, getMyProfile, type Profile as BackendProfile } from '../lib/api';
import { AppContext } from './appContextDef';
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
  AssistantChatMessage
} from '../types';
import {
  initialProfile,
  initialResumeDoc,
  initialJobs,
  initialApplications,
  initialResumeDrafts,
  initialCoverLetters,
  initialApprovals,
  initialCalendarEvents,
  initialInterviewSessions,
  initialFeedbackReport,
  initialRoadmapTasks,
  initialFollowUps,
  initialAssistantMessages
} from '../data/mockData';

const STORAGE_KEY = 'nexora_app_state_v1';

/** Safely parse persisted localStorage state; falls back to defaults on invalid JSON. */
function readStoredState<T>(suffix: string, fallback: T): T {
  try {
    const saved = localStorage.getItem(`${STORAGE_KEY}_${suffix}`);
    return saved ? (JSON.parse(saved) as T) : fallback;
  } catch {
    return fallback;
  }
}

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [backendProfile, setBackendProfile] = useState<BackendProfile | null>(null);
  const [backendProfileLoading, setBackendProfileLoading] = useState(false);
  const [backendProfileError, setBackendProfileError] = useState<string | null>(null);

  // Load initial state from localStorage or defaults
  const [profile, setProfile] = useState<StudentProfile>(() => readStoredState('profile', initialProfile));
  const [resumeDoc, setResumeDoc] = useState<ResumeDocument>(() => readStoredState('resume_doc', initialResumeDoc));
  const [jobs, setJobs] = useState<Job[]>(() => readStoredState('jobs', initialJobs));
  const [applications, setApplications] = useState<Application[]>(() => readStoredState('applications', initialApplications));
  const [resumeDrafts, setResumeDrafts] = useState<Record<string, ResumeDraft>>(() => readStoredState('resume_drafts', initialResumeDrafts));
  const [coverLetters, setCoverLetters] = useState<Record<string, CoverLetterDraft>>(() => readStoredState('cover_letters', initialCoverLetters));
  const [approvals, setApprovals] = useState<ApprovalItem[]>(() => readStoredState('approvals', initialApprovals));
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>(() => readStoredState('calendar', initialCalendarEvents));
  const [interviewSessions, setInterviewSessions] = useState<InterviewSession[]>(() => readStoredState('interviews', initialInterviewSessions));

  const [activeSession, setActiveSession] = useState<InterviewSession | null>(() => {
    return interviewSessions[0] || null;
  });

  const [feedbackReport, setFeedbackReport] = useState<FeedbackReport>(() => readStoredState('feedback', initialFeedbackReport));
  const [roadmapTasks, setRoadmapTasks] = useState<RoadmapTask[]>(() => readStoredState('roadmap', initialRoadmapTasks));
  const [followUps, setFollowUps] = useState<FollowUpItem[]>(() => readStoredState('followups', initialFollowUps));
  const [assistantMessages, setAssistantMessages] = useState<AssistantChatMessage[]>(() => readStoredState('assistant', initialAssistantMessages));

  // Sync to local storage
  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_profile`, JSON.stringify(profile));
  }, [profile]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_resume_doc`, JSON.stringify(resumeDoc));
  }, [resumeDoc]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_jobs`, JSON.stringify(jobs));
  }, [jobs]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_applications`, JSON.stringify(applications));
  }, [applications]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_resume_drafts`, JSON.stringify(resumeDrafts));
  }, [resumeDrafts]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_cover_letters`, JSON.stringify(coverLetters));
  }, [coverLetters]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_approvals`, JSON.stringify(approvals));
  }, [approvals]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_calendar`, JSON.stringify(calendarEvents));
  }, [calendarEvents]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_interviews`, JSON.stringify(interviewSessions));
  }, [interviewSessions]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_feedback`, JSON.stringify(feedbackReport));
  }, [feedbackReport]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_roadmap`, JSON.stringify(roadmapTasks));
  }, [roadmapTasks]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_followups`, JSON.stringify(followUps));
  }, [followUps]);

  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_assistant`, JSON.stringify(assistantMessages));
  }, [assistantMessages]);

  // Profile actions
  const updateProfile = (updated: Partial<StudentProfile>) => {
    setProfile(prev => {
      const next = { ...prev, ...updated };
      // Recalculate completeness
      let score = 50;
      if (next.skills.length >= 5) score += 15;
      if (next.projects.length >= 2) score += 15;
      if (next.experience.length >= 1) score += 10;
      if (next.links.github && next.links.linkedin) score += 10;
      next.completeness = Math.min(100, score);
      return next;
    });
  };

  const uploadResume = (file: { name: string; size: string }) => {
    const updated: ResumeDocument = {
      ...resumeDoc,
      fileName: file.name,
      fileSize: file.size,
      uploadedAt: new Date().toISOString(),
      lastParsedAt: new Date().toISOString(),
      verifiedByStudent: false
    };
    setResumeDoc(updated);
  };

  const verifySkill = (skillName: string) => {
    setResumeDoc(prev => ({
      ...prev,
      extractedSkills: prev.extractedSkills.map(s => 
        s.name.toLowerCase() === skillName.toLowerCase() ? { ...s, confirmed: true } : s
      )
    }));
    setProfile(prev => ({
      ...prev,
      skills: prev.skills.map(s => 
        s.name.toLowerCase() === skillName.toLowerCase() ? { ...s, verified: true } : s
      )
    }));
  };

  // Job actions
  const toggleSaveJob = (jobId: string) => {
    setJobs(prev => prev.map(j => j.id === jobId ? { ...j, saved: !j.saved } : j));
  };

  const getJobById = (jobId: string) => {
    return jobs.find(j => j.id === jobId);
  };

  // Application actions
  const updateApplicationStage = (applicationId: string, stage: ApplicationStage, note?: string) => {
    const today = '2026-11-10';
    setApplications(prev => prev.map(app => {
      if (app.id !== applicationId) return app;
      const timelineEvent = {
        id: `tl-${Date.now()}`,
        date: today,
        stage,
        note: note || `Stage updated to ${stage}.`,
        author: 'Student' as const
      };
      return {
        ...app,
        stage,
        lastUpdated: today,
        timeline: [timelineEvent, ...app.timeline]
      };
    }));
  };

  const createApplication = (jobId: string): Application => {
    const existing = applications.find(a => a.jobId === jobId);
    if (existing) return existing;

    const job = jobs.find(j => j.id === jobId);
    const today = '2026-11-10';
    const newApp: Application = {
      id: `app-${Date.now().toString().slice(-4)}`,
      jobId,
      jobTitle: job ? job.title : 'Software Engineer',
      company: job ? job.company : 'Company',
      location: job ? job.location : 'Bangalore',
      jobType: job ? job.type : 'Internship',
      dateAdded: today,
      deadline: job ? job.deadline : '2026-12-01',
      stage: 'Preparing',
      nextAction: 'Tailor resume and prepare application packet',
      nextActionDueDate: '2026-11-15',
      lastUpdated: today,
      notes: [`Application created from discovery on ${today}.`],
      timeline: [
        {
          id: `tl-${Date.now()}`,
          date: today,
          stage: 'Preparing',
          note: 'Started preparing application.',
          author: 'Student'
        }
      ]
    };

    setApplications(prev => [newApp, ...prev]);
    return newApp;
  };

  const getApplicationById = (applicationId: string) => {
    return applications.find(a => a.id === applicationId);
  };

  // Resume Studio actions
  const saveResumeDraft = (draft: ResumeDraft) => {
    setResumeDrafts(prev => ({
      ...prev,
      [draft.id]: { ...draft, updatedAt: new Date().toISOString() }
    }));
  };

  const updateBulletStatus = (draftId: string, type: 'experience' | 'project', id: string, status: 'accepted' | 'rejected') => {
    setResumeDrafts(prev => {
      const draft = prev[draftId];
      if (!draft) return prev;
      if (type === 'experience') {
        const nextHighlights = draft.experienceHighlights.map(h => {
          if (h.id === id) {
            return {
              ...h,
              status,
              bullet: status === 'accepted' && h.suggestion ? h.suggestion : h.originalBullet
            };
          }
          return h;
        });
        return {
          ...prev,
          [draftId]: { ...draft, experienceHighlights: nextHighlights }
        };
      } else {
        const nextHighlights = draft.projectHighlights.map(h => {
          if (h.id === id) {
            return {
              ...h,
              status,
              bullet: status === 'accepted' && h.suggestion ? h.suggestion : h.originalBullet
            };
          }
          return h;
        });
        return {
          ...prev,
          [draftId]: { ...draft, projectHighlights: nextHighlights }
        };
      }
    });
  };

  const submitResumeForApproval = (draft: ResumeDraft) => {
    saveResumeDraft({ ...draft, approvalStatus: 'pending_approval' });
    
    // Add or update in Approvals
    const existing = approvals.find(a => a.id === `appr-res-${draft.id}` || (a.type === 'tailored_resume' && a.jobId === draft.jobId));
    if (!existing) {
      const newApproval: ApprovalItem = {
        id: `appr-res-${draft.id}`,
        type: 'tailored_resume',
        title: `Tailored Resume for ${draft.company}`,
        jobId: draft.jobId,
        jobTitle: draft.jobTitle,
        company: draft.company,
        createdAt: new Date().toISOString(),
        status: 'pending',
        summary: `Customized bullet points and technical focus for ${draft.jobTitle}.`,
        changesCount: 2,
        unverifiedWarnings: ['Verify the highlighted project metrics match actual results.'],
        contentPreview: {
          afterText: draft.summary,
          highlights: draft.skills.filter(s => s.isHighlighted).map(s => s.name)
        }
      };
      setApprovals(prev => [newApproval, ...prev]);
    }
    
    // Update Application stage if applicable
    const app = applications.find(a => a.jobId === draft.jobId);
    if (app && app.stage === 'Preparing') {
      updateApplicationStage(app.id, 'Awaiting approval', 'Tailored resume submitted to Approval Centre.');
    }
  };

  // Cover letter actions
  const saveCoverLetter = (letter: CoverLetterDraft) => {
    setCoverLetters(prev => ({
      ...prev,
      [letter.id]: letter
    }));
  };

  const submitCoverLetterForApproval = (letter: CoverLetterDraft) => {
    saveCoverLetter({ ...letter, approvalStatus: 'pending_approval' });
    const existing = approvals.find(a => a.type === 'cover_letter' && a.jobId === letter.jobId);
    if (!existing) {
      const newApproval: ApprovalItem = {
        id: `appr-cov-${letter.id}`,
        type: 'cover_letter',
        title: `Cover Letter for ${letter.company}`,
        jobId: letter.jobId,
        jobTitle: letter.jobTitle,
        company: letter.company,
        createdAt: new Date().toISOString(),
        status: 'pending',
        summary: `Targeted ${letter.wordCount}-word cover letter highlighting relevant systems background.`,
        changesCount: 1,
        unverifiedWarnings: [],
        contentPreview: {
          afterText: letter.bodyParagraph1,
          highlights: ['Custom Introduction', 'Value alignment']
        }
      };
      setApprovals(prev => [newApproval, ...prev]);
    }
  };

  // Approval actions
  const approveItem = (approvalId: string) => {
    setApprovals(prev => prev.map(a => a.id === approvalId ? { ...a, status: 'approved' } : a));
    
    const item = approvals.find(a => a.id === approvalId);
    if (!item) return;

    // Advance associated application if suitable
    const app = applications.find(a => a.jobId === item.jobId);
    if (app) {
      if (item.type === 'tailored_resume' || item.type === 'cover_letter') {
        updateApplicationStage(app.id, 'Ready to apply', `${item.title} explicitly approved by student.`);
      }
    }
  };

  const rejectItem = (approvalId: string) => {
    setApprovals(prev => prev.map(a => a.id === approvalId ? { ...a, status: 'rejected' } : a));
  };

  // Calendar actions
  const addCalendarEvent = (event: Omit<CalendarEvent, 'id'>) => {
    const newEvent: CalendarEvent = {
      ...event,
      id: `cal-${Date.now()}`
    };
    setCalendarEvents(prev => [newEvent, ...prev]);
  };

  const toggleEventCompletion = (eventId: string) => {
    setCalendarEvents(prev => prev.map(e => e.id === eventId ? { ...e, completed: !e.completed } : e));
  };

  // Interview actions
  const startNewSession = (
    role: string,
    company: string,
    type: 'Technical' | 'Behavioural' | 'HR' | 'Role-specific',
    difficulty: 'Junior' | 'Mid' | 'Challenging'
  ): string => {
    const newId = `session-${Date.now().toString().slice(-4)}`;
    const questions = [
      {
        id: 'q-101',
        question: `How would you architect a fault-tolerant caching layer for ${company}'s high-throughput endpoints?`,
        category: 'System Design' as const,
        hint: 'Discuss cache eviction policies (LRU), write-through vs cache-aside, and cache stampede prevention.',
        contextWhyAsked: `Evaluates production architecture thinking for ${role}.`,
        sampleFramework: 'Cache-aside pattern -> Distributed locks for mutex warming -> Circuit breaker fallback to primary DB.'
      },
      {
        id: 'q-102',
        question: 'Describe a situation where an asynchronous queue experienced high backpressure. How would you debug and mitigate it?',
        category: 'Technical' as const,
        hint: 'Examine worker thread pools, batch processing, autoscaling, and queue depth alerts.',
        contextWhyAsked: 'Tests practical troubleshooting of asynchronous architectures.',
        sampleFramework: 'Identify bottleneck metric (inflow vs processing rate) -> Scale consumers -> Apply rate-limiting at ingress.'
      },
      {
        id: 'q-103',
        question: 'Tell me about a technical disagreement you had regarding architecture. How did you resolve it objectively?',
        category: 'Behavioural' as const,
        hint: 'Use the STAR method: Situation, Task, Action with data/benchmarks, and positive outcome.',
        contextWhyAsked: 'Measures collaborative communication and engineering rigor.',
        sampleFramework: 'Present opposing views -> Benchmark with quantitative metrics -> Agree on trade-offs.'
      }
    ];

    const session: InterviewSession = {
      id: newId,
      role,
      company,
      type,
      difficulty,
      questions,
      currentQuestionIndex: 0,
      startedAt: new Date().toISOString(),
      status: 'in_progress'
    };

    setInterviewSessions(prev => [session, ...prev]);
    setActiveSession(session);
    return newId;
  };

  const submitAnswer = (sessionId: string, questionIndex: number, answer: string) => {
    setInterviewSessions(prev => prev.map(s => {
      if (s.id !== sessionId) return s;
      const updatedQuestions = [...s.questions];
      if (updatedQuestions[questionIndex]) {
        updatedQuestions[questionIndex] = {
          ...updatedQuestions[questionIndex],
          studentAnswer: answer
        };
      }
      return { ...s, questions: updatedQuestions };
    }));

    if (activeSession && activeSession.id === sessionId) {
      const updated = { ...activeSession };
      if (updated.questions[questionIndex]) {
        updated.questions[questionIndex].studentAnswer = answer;
      }
      setActiveSession(updated);
    }
  };

  const completeSession = (sessionId: string) => {
    const today = '2026-11-10';
    setInterviewSessions(prev => prev.map(s => {
      if (s.id !== sessionId) return s;
      return { ...s, status: 'completed', completedAt: new Date().toISOString() };
    }));

    // Generate dynamic feedback report
    const targetSession = interviewSessions.find(s => s.id === sessionId) || activeSession;
    if (targetSession) {
      const report: FeedbackReport = {
        id: `rep-${Date.now()}`,
        sessionId,
        role: targetSession.role,
        company: targetSession.company,
        interviewType: `${targetSession.type} Practice`,
        completedDate: today,
        overallScore: 86,
        scores: {
          communication: 88,
          technical: 85,
          relevance: 89,
          clarity: 84,
          delivery: 80
        },
        overallAssessment: `Strong technical comprehension of system trade-offs for ${targetSession.company}. Answers were anchored in real architectural decisions rather than theoretical abstractions.`,
        strongPoints: [
          'Effective decomposition of cache stampede protection and fallback strategies.',
          'Pragmatic understanding of backpressure mechanics in distributed queues.',
          'Structured answer delivery following clear problem-solving sequences.'
        ],
        areasToImprove: [
          'Quantify capacity sizing (e.g. estimating throughput in requests/sec and memory in GB).',
          'Mention observability dashboards and telemetry signals (p99 latency, queue lag).',
          'Conclude behavioral stories with lasting operational takeaways.'
        ],
        recommendedNextPractice: 'Practice quantitative capacity estimation and latency budget breakdowns.',
        questionFeedback: targetSession.questions.map((q, idx) => ({
          questionId: q.id,
          questionText: q.question,
          studentAnswer: q.studentAnswer || 'Provided verbal response during practice session.',
          score: 82 + (idx * 3),
          critique: 'Addressed core engineering principles with sound reasoning.',
          improvedApproach: 'Include concrete numerical bounds (e.g., target 99.9% uptime and <20ms cache latency).'
        }))
      };
      setFeedbackReport(report);
    }
  };

  // Roadmap actions
  const updateTaskStatus = (taskId: string, status: 'Not started' | 'In progress' | 'Completed') => {
    setRoadmapTasks(prev => prev.map(t => t.id === taskId ? { ...t, status } : t));
  };

  const addRoadmapTask = (task: Omit<RoadmapTask, 'id' | 'status' | 'relatedJobCount'>) => {
    const newTask: RoadmapTask = {
      ...task,
      id: `task-rm-${Date.now()}`,
      status: 'Not started',
      relatedJobCount: 2
    };
    setRoadmapTasks(prev => [newTask, ...prev]);
  };

  // Follow-up actions
  const saveFollowUpDraft = (followUp: FollowUpItem) => {
    setFollowUps(prev => prev.map(f => f.id === followUp.id ? followUp : f));
  };

  const requestFollowUpApproval = (followUpId: string) => {
    setFollowUps(prev => prev.map(f => f.id === followUpId ? { ...f, status: 'awaiting_approval' } : f));
    const fu = followUps.find(f => f.id === followUpId);
    if (fu) {
      const newApproval: ApprovalItem = {
        id: `appr-fu-${fu.id}`,
        type: 'follow_up',
        title: `Follow-up Email to ${fu.company}`,
        jobId: fu.applicationId,
        jobTitle: fu.role,
        company: fu.company,
        createdAt: new Date().toISOString(),
        status: 'pending',
        summary: `Follow-up message to ${fu.recipientName} regarding ${fu.role}.`,
        changesCount: 1,
        unverifiedWarnings: [],
        contentPreview: {
          afterText: fu.message,
          highlights: ['Polite Follow-up', 'Application Status']
        }
      };
      setApprovals(prev => [newApproval, ...prev]);
    }
  };

  // Assistant actions
  const sendMessageToAssistant = (text: string) => {
    const userMsg: AssistantChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      content: text
    };

    setAssistantMessages(prev => [...prev, userMsg]);

    // Generate intelligent contextual response
    setTimeout(() => {
      let reply = "I'm here to help you advance your placement journey. Let's look at your active applications and next steps.";
      let actionLink: { label: string; to: string } | undefined = undefined;
      const lower = text.toLowerCase();

      if (lower.includes('vercel') || lower.includes('resume draft') || lower.includes('approval')) {
        reply = "Your tailored resume for **Vercel Software Engineer Intern** is ready in the Approval Centre. It highlights your frontend component architecture from the Campus Marketplace project and your 38% latency optimization at InnovateCloud Labs. Remember to verify the metrics before approving!";
        actionLink = { label: 'Go to Approval Centre', to: '/app/approvals' };
      } else if (lower.includes('stripe') || lower.includes('interview') || lower.includes('round 2')) {
        reply = "For your **Stripe Round 2 Systems Architecture** interview on Saturday, Nov 15:\n\n1. Review pessimistic vs optimistic locking for concurrent transactions.\n2. Prepare your walkthrough of the Redis task runner heartbeat logic.\n3. Make sure to complete the follow-up confirmation note.";
        actionLink = { label: 'Start Systems Practice', to: '/app/interview-prep' };
      } else if (lower.includes('datadog') || lower.includes('missing') || lower.includes('skill')) {
        reply = "For the **Datadog Platform Infrastructure Intern** role, your fit score is 78%. The main skill gaps are **Apache Kafka** and **Kubernetes containerization**. Both are actively tracked on your Skill Roadmap with curated documentation.";
        actionLink = { label: 'View Skill Roadmap', to: '/app/skill-roadmap' };
      } else if (lower.includes('atlassian') || lower.includes('hackerrank') || lower.includes('assessment')) {
        reply = "Your **Atlassian coding challenge** deadline is **November 14 at 23:59 IST**. Review Graph traversal (BFS/DFS) and dynamic programming before opening the 90-minute HackerRank link.";
        actionLink = { label: 'View Application', to: '/app/applications/app-002' };
      }

      const botMsg: AssistantChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        content: reply,
        actionLink
      };

      setAssistantMessages(prev => [...prev, botMsg]);
    }, 400);
  };

  const refreshBackendProfile = useCallback(async () => {
    setBackendProfileLoading(true);
    setBackendProfileError(null);
    try {
      const data = await getMyProfile();
      setBackendProfile(data);
      setProfile(prev => ({
        ...prev,
        id: data.id,
        email: data.email ?? prev.email,
        fullName: data.full_name ?? prev.fullName,
        branch: data.branch ?? prev.branch,
        graduationYear: data.batch_year ? String(data.batch_year) : prev.graduationYear,
      }));
    } catch (err) {
      setBackendProfile(null);
      setBackendProfileError(
        err instanceof ApiError ? `${err.code}: ${err.message}` : 'Could not reach the API.'
      );
    } finally {
      setBackendProfileLoading(false);
    }
  }, []);

  const effectiveProfile = useMemo<StudentProfile>(() => {
    if (!user?.email) return profile;
    return {
      ...profile,
      id: user.id,
      email: user.email,
    };
  }, [profile, user]);

  const activeBackendProfile = user ? backendProfile : null;
  const activeBackendProfileError = user ? backendProfileError : null;

  const resetDemoData = () => {
    localStorage.clear();
    setProfile(initialProfile);
    setResumeDoc(initialResumeDoc);
    setJobs(initialJobs);
    setApplications(initialApplications);
    setResumeDrafts(initialResumeDrafts);
    setCoverLetters(initialCoverLetters);
    setApprovals(initialApprovals);
    setCalendarEvents(initialCalendarEvents);
    setInterviewSessions(initialInterviewSessions);
    setActiveSession(initialInterviewSessions[0]);
    setFeedbackReport(initialFeedbackReport);
    setRoadmapTasks(initialRoadmapTasks);
    setFollowUps(initialFollowUps);
    setAssistantMessages(initialAssistantMessages);
  };

  return (
    <AppContext.Provider
      value={{
        profile: effectiveProfile,
        updateProfile,
        resumeDoc,
        uploadResume,
        verifySkill,
        jobs,
        toggleSaveJob,
        getJobById,
        applications,
        updateApplicationStage,
        createApplication,
        getApplicationById,
        resumeDrafts,
        saveResumeDraft,
        updateBulletStatus,
        submitResumeForApproval,
        coverLetters,
        saveCoverLetter,
        submitCoverLetterForApproval,
        approvals,
        approveItem,
        rejectItem,
        calendarEvents,
        addCalendarEvent,
        toggleEventCompletion,
        interviewSessions,
        activeSession,
        startNewSession,
        submitAnswer,
        completeSession,
        feedbackReport,
        roadmapTasks,
        updateTaskStatus,
        addRoadmapTask,
        followUps,
        saveFollowUpDraft,
        requestFollowUpApproval,
        assistantMessages,
        sendMessageToAssistant,
        resetDemoData,
        backendProfile: activeBackendProfile,
        backendProfileLoading,
        backendProfileError: activeBackendProfileError,
        refreshBackendProfile
      }}
    >
      {children}
    </AppContext.Provider>
  );
};
