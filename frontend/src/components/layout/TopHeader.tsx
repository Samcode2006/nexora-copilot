import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  Bell,
  Search,
  Menu,
  User,
  Settings,
  ChevronDown,
  Calendar,
  AlertCircle,
  Target
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { useAuth } from '../../auth/AuthContext';

export const TopHeader: React.FC<{
  onOpenMobile: () => void;
  collapsed: boolean;
}> = ({ onOpenMobile }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { profile, calendarEvents, approvals } = useApp();
  const { user, signOut } = useAuth();

  const [notificationOpen, setNotificationOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const notificationRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (notificationRef.current && !notificationRef.current.contains(e.target as Node)) {
        setNotificationOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getRouteTitle = () => {
    const path = location.pathname;
    if (path.includes('/dashboard')) return { title: 'Dashboard', category: 'Overview' };
    if (path.includes('/jobs')) return { title: 'Find Opportunities', category: 'Discovery' };
    if (path.includes('/resume-studio')) return { title: 'Resume Studio', category: 'Documents' };
    if (path.includes('/cover-letter')) return { title: 'Cover Letters', category: 'Documents' };
    if (path.includes('/approvals')) return { title: 'Approval Centre', category: 'Review' };
    if (path.includes('/applications')) return { title: 'My Applications', category: 'Pipeline' };
    if (path.includes('/calendar')) return { title: 'Placement Calendar', category: 'Schedule' };
    if (path.includes('/interview-prep')) return { title: 'Interview Preparation', category: 'Readiness' };
    if (path.includes('/feedback')) return { title: 'Interview Feedback', category: 'Assessment' };
    if (path.includes('/skill-roadmap')) return { title: 'Skill Roadmap', category: 'Improvement' };
    if (path.includes('/follow-ups')) return { title: 'Follow-up Assistant', category: 'Communications' };
    if (path.includes('/assistant')) return { title: 'Nexora Assistant', category: 'Co-pilot' };
    if (path.includes('/profile')) return { title: 'Student Profile', category: 'Personal' };
    if (path.includes('/resume')) return { title: 'Resume Management', category: 'Documents' };
    if (path.includes('/settings')) return { title: 'Settings', category: 'Preferences' };
    return { title: 'Nexora', category: 'Career Co-pilot' };
  };

  const { title, category } = getRouteTitle();
  const upcomingEvents = calendarEvents.slice(0, 3);
  const pendingApprovalsCount = approvals.filter(a => a.status === 'pending').length;

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/app/jobs?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="h-16 bg-[#F4F2EC] px-4 md:px-6 flex items-center justify-between sticky top-0 z-30 shrink-0 border-b border-black/[0.06]">
      {/* Left: Mobile trigger & breadcrumb */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobile}
          aria-label="Open mobile navigation"
          className="lg:hidden p-2 rounded-xl text-charcoal-600 hover:text-charcoal-900 hover:bg-black/5"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-baseline gap-2">
          <span className="text-[11px] font-bold text-coral-600 uppercase tracking-wider hidden sm:inline">
            {category}
          </span>
          <span className="text-charcoal-300 hidden sm:inline">/</span>
          <h1 className="text-sm md:text-base font-extrabold text-charcoal-900 tracking-tight">{title}</h1>
        </div>
      </div>

      {/* Middle: Clean Pill Search Input (Inspired by Image 2) */}
      <form onSubmit={handleSearchSubmit} className="hidden md:flex items-center max-w-sm w-full mx-4">
        <div className="relative w-full">
          <Search className="w-3.5 h-3.5 text-charcoal-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search roles, skills, or companies..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white/90 border border-charcoal-200/80 rounded-full py-1.5 pl-9 pr-3 text-xs text-charcoal-900 placeholder-charcoal-500 focus:outline-none focus:border-coral-500 focus:bg-white shadow-subtle transition-all"
          />
        </div>
      </form>

      {/* Right: Dribbble-style Readiness & Streak Pills + Avatar */}
      <div className="flex items-center gap-2.5">
        {/* Readiness Pill (e.g., 88% Ready) */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-charcoal-200/80 text-xs font-semibold text-charcoal-800 shadow-subtle">
          <Target className="w-3.5 h-3.5 text-coral-500" />
          <span>{profile.completeness}% Ready</span>
        </div>

        {/* Stripe Countdown Pill */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-charcoal-200/80 text-xs font-semibold text-charcoal-800 shadow-subtle">
          <Calendar className="w-3.5 h-3.5 text-ochre-500" />
          <span>Nov 15 • Stripe</span>
        </div>

        {/* Approvals quick pill */}
        {pendingApprovalsCount > 0 && (
          <Link
            to="/app/approvals"
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-coral-50 text-coral-700 border border-coral-200 hover:bg-coral-100 transition-colors shadow-subtle"
          >
            <AlertCircle className="w-3.5 h-3.5 text-coral-500" />
            <span>{pendingApprovalsCount} to approve</span>
          </Link>
        )}

        {/* Notifications Popover */}
        <div className="relative" ref={notificationRef}>
          <button
            onClick={() => setNotificationOpen(!notificationOpen)}
            aria-label="Notifications"
            className="p-2 rounded-full bg-white border border-charcoal-200/80 text-charcoal-600 hover:text-charcoal-900 hover:shadow-subtle transition-all"
          >
            <Bell className="w-4 h-4" />
          </button>

          {notificationOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-charcoal-200/80 rounded-2xl shadow-dropdown p-0 overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="px-4 py-3 border-b border-charcoal-100 flex items-center justify-between bg-sand-50">
                <span className="text-xs font-bold text-charcoal-900">Notifications & Deadlines</span>
                <Link
                  to="/app/calendar"
                  onClick={() => setNotificationOpen(false)}
                  className="text-[11px] text-coral-600 font-semibold hover:underline"
                >
                  View calendar
                </Link>
              </div>

              <div className="divide-y divide-charcoal-100 max-h-72 overflow-y-auto">
                {upcomingEvents.map((evt) => (
                  <div key={evt.id} className="p-3 text-xs hover:bg-canvas-50 transition-colors">
                    <div className="flex items-start gap-2">
                      <Calendar className="w-3.5 h-3.5 text-coral-500 shrink-0 mt-0.5" />
                      <div>
                        <p className="font-bold text-charcoal-900 leading-snug">{evt.title}</p>
                        <p className="text-[11px] text-charcoal-600 mt-0.5">
                          {evt.date} {evt.time ? `• ${evt.time}` : ''}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User avatar & dropdown */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 p-1 rounded-full hover:bg-white transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-navy-900 text-white font-bold text-xs flex items-center justify-center shadow-subtle ring-2 ring-white">
              {profile.fullName.charAt(0)}
            </div>
            <ChevronDown className="w-3 h-3 text-charcoal-500" />
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-white border border-charcoal-200 rounded-2xl shadow-dropdown p-1.5 overflow-hidden z-50 text-xs animate-in fade-in zoom-in-95 duration-100">
              <div className="px-3 py-2.5 border-b border-charcoal-100">
                <p className="font-bold text-charcoal-900">{profile.fullName}</p>
                <p className="text-[11px] text-charcoal-600 truncate">{user?.email || profile.college}</p>
              </div>

              <div className="py-1">
                <Link
                  to="/app/profile"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 text-charcoal-700 hover:bg-canvas-100 rounded-xl transition-colors font-medium"
                >
                  <User className="w-3.5 h-3.5 text-charcoal-500" />
                  <span>My Profile</span>
                </Link>

                <Link
                  to="/app/settings"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 text-charcoal-700 hover:bg-canvas-100 rounded-xl transition-colors font-medium"
                >
                  <Settings className="w-3.5 h-3.5 text-charcoal-500" />
                  <span>Settings</span>
                </Link>
              </div>

              <div className="pt-1 border-t border-charcoal-100">
                <button
                  type="button"
                  onClick={async () => {
                    setUserMenuOpen(false);
                    await signOut();
                    navigate('/login', { replace: true });
                  }}
                  className="w-full text-left flex items-center gap-2 px-3 py-2 text-charcoal-600 hover:bg-canvas-100 rounded-xl transition-colors"
                >
                  <span>Sign out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
