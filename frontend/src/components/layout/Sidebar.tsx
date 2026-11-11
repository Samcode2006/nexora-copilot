import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  FileEdit,
  Mail,
  FolderGit2,
  CheckSquare,
  Send,
  Calendar,
  Sparkles,
  Compass,
  FileText,
  User,
  Settings,
  Bot,
  ChevronLeft,
  ChevronRight,
  GraduationCap
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { cn } from '../../lib/utils';

interface NavItem {
  name: string;
  path: string;
  icon: React.ElementType;
  badge?: number | string;
  badgeVariant?: 'default' | 'amber' | 'coral';
}

interface NavGroup {
  group: string;
  items: NavItem[];
}

export const Sidebar: React.FC<{
  collapsed: boolean;
  onToggleCollapse: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}> = ({ collapsed, onToggleCollapse, mobileOpen, onCloseMobile }) => {
  const location = useLocation();
  const { approvals, applications, profile } = useApp();

  const pendingApprovalsCount = approvals.filter(a => a.status === 'pending').length;
  const activeApplicationsCount = applications.filter(a => !['Rejected', 'Withdrawn', 'Offer'].includes(a.stage)).length;

  const navigation: NavGroup[] = [
    {
      group: 'OVERVIEW',
      items: [
        { name: 'Dashboard', path: '/app/dashboard', icon: LayoutDashboard }
      ]
    },
    {
      group: 'OPPORTUNITIES',
      items: [
        { name: 'Find Jobs', path: '/app/jobs', icon: Briefcase },
        { name: 'Resume Studio', path: '/app/resume-studio', icon: FileEdit },
        { name: 'Cover Letters', path: '/app/cover-letter', icon: Mail }
      ]
    },
    {
      group: 'APPLICATIONS',
      items: [
        {
          name: 'My Applications',
          path: '/app/applications',
          icon: FolderGit2,
          badge: activeApplicationsCount > 0 ? activeApplicationsCount : undefined
        },
        {
          name: 'Approvals',
          path: '/app/approvals',
          icon: CheckSquare,
          badge: pendingApprovalsCount > 0 ? pendingApprovalsCount : undefined,
          badgeVariant: 'coral'
        },
        { name: 'Follow-ups', path: '/app/follow-ups', icon: Send },
        { name: 'Calendar', path: '/app/calendar', icon: Calendar }
      ]
    },
    {
      group: 'PREPARATION',
      items: [
        { name: 'Interview Prep', path: '/app/interview-prep', icon: Sparkles },
        { name: 'Skill Roadmap', path: '/app/skill-roadmap', icon: Compass },
        { name: 'Feedback', path: '/app/feedback', icon: FileText }
      ]
    },
    {
      group: 'PERSONAL',
      items: [
        { name: 'My Profile', path: '/app/profile', icon: User },
        { name: 'Resume', path: '/app/resume', icon: FileText },
        { name: 'Nexora Assistant', path: '/app/assistant', icon: Bot },
        { name: 'Settings', path: '/app/settings', icon: Settings }
      ]
    }
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-navy-950/60 backdrop-blur-xs z-40 lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 bg-navy-900 text-slate-200 transition-all duration-200 ease-in-out border-r border-white/10 flex flex-col shadow-hero",
          collapsed ? "w-18" : "w-64",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Brand header */}
        <div className="h-16 border-b border-white/10 flex items-center justify-between px-5 shrink-0">
          <NavLink to="/app/dashboard" className="flex items-center gap-3 overflow-hidden">
            <div className="w-8 h-8 rounded-xl bg-coral-500 text-white flex items-center justify-center shrink-0 font-bold text-base shadow-card">
              <GraduationCap className="w-5 h-5" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-extrabold tracking-tight text-white text-base">NEXORA</span>
                <span className="text-[10px] text-slate-400 font-medium tracking-tight -mt-0.5">Placement Co-pilot</span>
              </div>
            )}
          </NavLink>

          <button
            onClick={onToggleCollapse}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="hidden lg:flex items-center justify-center w-7 h-7 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation items list */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden py-4 px-3 space-y-5 text-xs">
          {navigation.map((group) => (
            <div key={group.group}>
              {!collapsed && (
                <div className="px-3 pb-1.5 text-[10px] font-bold tracking-widest text-slate-400 uppercase">
                  {group.group}
                </div>
              )}
              <div className="space-y-1">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path || (item.path !== '/app/dashboard' && location.pathname.startsWith(item.path));
                  
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={onCloseMobile}
                      title={collapsed ? item.name : undefined}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-150 group relative text-xs font-medium",
                        isActive
                          ? "bg-white/15 text-white font-bold shadow-subtle border border-white/10"
                          : "text-slate-300 hover:text-white hover:bg-white/5"
                      )}
                    >
                      <Icon className={cn("w-4 h-4 shrink-0 transition-colors", isActive ? "text-coral-400" : "text-slate-400 group-hover:text-slate-200")} />
                      {!collapsed && <span className="truncate">{item.name}</span>}

                      {/* Badge count */}
                      {!collapsed && item.badge !== undefined && (
                        <span
                          className={cn(
                            "ml-auto px-2 py-0.5 rounded-full text-[10px] font-extrabold leading-none",
                            item.badgeVariant === 'coral'
                              ? "bg-coral-500 text-white shadow-subtle"
                              : "bg-white/20 text-slate-200"
                          )}
                        >
                          {item.badge}
                        </span>
                      )}

                      {/* Dot for collapsed sidebar badge */}
                      {collapsed && item.badge !== undefined && (
                        <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-coral-400" />
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Sidebar footer status */}
        <div className="p-3.5 border-t border-white/10 text-slate-300 shrink-0">
          {!collapsed ? (
            <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Season Active</span>
              </span>
              <span 
                className="text-slate-400 font-mono text-[10px] truncate max-w-[110px]" 
                title={profile.college || 'Universal'}
              >
                {profile.college ? (profile.college.includes(',') ? profile.college.split(',')[0] : profile.college) : 'All Colleges'}
              </span>
            </div>
          ) : (
            <div className="flex justify-center">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="Placement Active" />
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
