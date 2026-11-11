import { createBrowserRouter, Navigate } from 'react-router-dom';

// Auth Guards
import { RequireAuth, RedirectIfAuthenticated } from '../auth/RequireAuth';

// Layouts
import { AppLayout } from '../components/layout/AppLayout';
import { OnboardingLayout } from '../features/onboarding/OnboardingLayout';

// Public pages
import { LandingPage } from '../features/landing/LandingPage';
import { LoginPage } from '../features/auth/LoginPage';
import { SignupPage } from '../features/auth/SignupPage';
import { ForgotPasswordPage } from '../features/auth/ForgotPasswordPage';

// Onboarding steps
import { StepProfile } from '../features/onboarding/StepProfile';
import { StepResume } from '../features/onboarding/StepResume';
import { StepPreferences } from '../features/onboarding/StepPreferences';
import { StepComplete } from '../features/onboarding/StepComplete';

// Main App pages
import { DashboardPage } from '../features/dashboard/DashboardPage';
import { ProfilePage } from '../features/profile/ProfilePage';
import { ResumeManagementPage } from '../features/resume/ResumeManagementPage';
import { JobsDiscoveryPage } from '../features/jobs/JobsDiscoveryPage';
import { JobDetailPage } from '../features/jobs/JobDetailPage';
import { ResumeStudioPage } from '../features/resume-studio/ResumeStudioPage';
import { CoverLetterPage } from '../features/cover-letter/CoverLetterPage';
import { ApprovalCentrePage } from '../features/approvals/ApprovalCentrePage';
import { ApplicationTrackerPage } from '../features/applications/ApplicationTrackerPage';
import { ApplicationDetailPage } from '../features/applications/ApplicationDetailPage';
import { CalendarPage } from '../features/calendar/CalendarPage';
import { InterviewPrepPage } from '../features/interview/InterviewPrepPage';
import { InterviewSessionPage } from '../features/interview/InterviewSessionPage';
import { InterviewFeedbackPage } from '../features/feedback/InterviewFeedbackPage';
import { SkillRoadmapPage } from '../features/roadmap/SkillRoadmapPage';
import { FollowUpAssistantPage } from '../features/follow-ups/FollowUpAssistantPage';
import { AssistantPage } from '../features/assistant/AssistantPage';
import { SettingsPage } from '../features/settings/SettingsPage';

export const router = createBrowserRouter([
  // Public Routes
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/login',
    element: (
      <RedirectIfAuthenticated>
        <LoginPage />
      </RedirectIfAuthenticated>
    ),
  },
  {
    path: '/signup',
    element: (
      <RedirectIfAuthenticated>
        <SignupPage />
      </RedirectIfAuthenticated>
    ),
  },
  {
    path: '/forgot-password',
    element: <ForgotPasswordPage />,
  },

  // Protected Routes (requires Supabase Auth session)
  {
    element: <RequireAuth />,
    children: [
      // Onboarding Routes
      {
        path: '/onboarding',
        element: <OnboardingLayout />,
        children: [
          {
            index: true,
            element: <Navigate to="/onboarding/profile" replace />,
          },
          {
            path: 'profile',
            element: <StepProfile />,
          },
          {
            path: 'resume',
            element: <StepResume />,
          },
          {
            path: 'preferences',
            element: <StepPreferences />,
          },
          {
            path: 'complete',
            element: <StepComplete />,
          },
        ],
      },

      // Authenticated App Shell Routes
      {
        path: '/app',
        element: <AppLayout />,
        children: [
          {
            index: true,
            element: <Navigate to="/app/dashboard" replace />,
          },
          {
            path: 'dashboard',
            element: <DashboardPage />,
          },
          {
            path: 'profile',
            element: <ProfilePage />,
          },
          {
            path: 'resume',
            element: <ResumeManagementPage />,
          },
          {
            path: 'jobs',
            element: <JobsDiscoveryPage />,
          },
          {
            path: 'jobs/:jobId',
            element: <JobDetailPage />,
          },
          {
            path: 'resume-studio',
            element: <ResumeStudioPage />,
          },
          {
            path: 'cover-letter',
            element: <CoverLetterPage />,
          },
          {
            path: 'approvals',
            element: <ApprovalCentrePage />,
          },
          {
            path: 'applications',
            element: <ApplicationTrackerPage />,
          },
          {
            path: 'applications/:applicationId',
            element: <ApplicationDetailPage />,
          },
          {
            path: 'calendar',
            element: <CalendarPage />,
          },
          {
            path: 'interview-prep',
            element: <InterviewPrepPage />,
          },
          {
            path: 'interview-prep/:sessionId',
            element: <InterviewSessionPage />,
          },
          {
            path: 'feedback',
            element: <InterviewFeedbackPage />,
          },
          {
            path: 'skill-roadmap',
            element: <SkillRoadmapPage />,
          },
          {
            path: 'follow-ups',
            element: <FollowUpAssistantPage />,
          },
          {
            path: 'assistant',
            element: <AssistantPage />,
          },
          {
            path: 'settings',
            element: <SettingsPage />,
          },
        ],
      },
    ],
  },

  // Fallback Catch-all
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
