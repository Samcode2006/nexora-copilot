import React, { type ReactNode } from 'react';
import { cn } from '../../lib/utils';
import type { ApplicationStage, MatchCategory } from '../../types';

// Button Component
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'coral' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success' | 'glass';
  size?: 'sm' | 'md' | 'lg';
  children: ReactNode;
  icon?: ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  className,
  children,
  icon,
  disabled,
  ...props
}) => {
  const base = "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-coral-400/40 disabled:opacity-50 disabled:pointer-events-none select-none text-xs md:text-sm active:scale-[0.98]";
  
  const sizes = {
    sm: "px-3 py-1.5 text-xs gap-1.5",
    md: "px-4 py-2 text-xs md:text-sm gap-2",
    lg: "px-6 py-3 text-sm md:text-base gap-2.5 font-semibold"
  };

  const variants = {
    // Primary is the bold Dribbble warm coral
    primary: "bg-coral-500 text-white hover:bg-coral-600 active:bg-coral-700 shadow-card hover:shadow-float border border-coral-400/30",
    coral: "bg-coral-500 text-white hover:bg-coral-600 active:bg-coral-700 shadow-card hover:shadow-float border border-coral-400/30",
    secondary: "bg-navy-900 text-white hover:bg-navy-800 active:bg-navy-950 shadow-subtle border border-navy-700/50",
    outline: "bg-white text-charcoal-800 border border-charcoal-200 hover:bg-canvas-100 hover:border-charcoal-300 shadow-subtle",
    ghost: "text-charcoal-700 hover:bg-black/5 active:bg-black/10",
    glass: "bg-white/10 text-white hover:bg-white/15 border border-white/20 backdrop-blur-md",
    danger: "bg-red-600 text-white hover:bg-red-700 border border-red-700/30 shadow-subtle",
    success: "bg-emerald-600 text-white hover:bg-emerald-700 border border-emerald-700/30 shadow-subtle"
  };

  return (
    <button
      className={cn(base, sizes[size], variants[variant], className)}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </button>
  );
};

// Card / Panel Component
export const Panel: React.FC<{
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}> = ({ children, className, onClick }) => {
  return (
    <div
      onClick={onClick}
      className={cn(
        "bg-white border border-charcoal-200/70 rounded-2xl shadow-card overflow-hidden transition-all duration-200",
        onClick && "cursor-pointer hover:border-charcoal-300 hover:shadow-float hover:-translate-y-0.5",
        className
      )}
    >
      {children}
    </div>
  );
};

export const PanelHeader: React.FC<{
  title: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
}> = ({ title, subtitle, action, className }) => {
  return (
    <div className={cn("px-5 py-4 border-b border-charcoal-100 flex items-center justify-between bg-white", className)}>
      <div>
        <h3 className="font-bold text-charcoal-900 text-sm tracking-tight">{title}</h3>
        {subtitle && <p className="text-xs text-charcoal-500 mt-0.5 font-normal">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
};

export const PanelBody: React.FC<{ children: ReactNode; className?: string }> = ({
  children,
  className
}) => {
  return <div className={cn("p-5 md:p-6", className)}>{children}</div>;
};

// Stage Badge Component
export const StageBadge: React.FC<{ stage: ApplicationStage; size?: 'sm' | 'md' }> = ({
  stage,
  size = 'md'
}) => {
  const getStyle = () => {
    switch (stage) {
      case 'Interested':
        return 'bg-canvas-200 text-charcoal-700 border-charcoal-300';
      case 'Preparing':
        return 'bg-ochre-50 text-ochre-700 border-ochre-200 font-medium';
      case 'Awaiting approval':
        return 'bg-coral-50 text-coral-700 border-coral-200 font-semibold';
      case 'Ready to apply':
        return 'bg-blue-50 text-blue-700 border-blue-200 font-medium';
      case 'Applied':
        return 'bg-steel-50 text-steel-700 border-steel-200 font-medium';
      case 'Assessment':
        return 'bg-violet-50 text-violet-700 border-violet-200 font-semibold';
      case 'Interview':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200 font-bold';
      case 'Offer':
        return 'bg-emerald-100 text-emerald-900 border-emerald-300 font-bold';
      case 'Rejected':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'Withdrawn':
        return 'bg-charcoal-100 text-charcoal-600 border-charcoal-200';
      default:
        return 'bg-charcoal-100 text-charcoal-700 border-charcoal-200';
    }
  };

  return (
    <span
      className={cn(
        "inline-flex items-center border rounded-full font-medium tracking-tight whitespace-nowrap",
        size === 'sm' ? "px-2.5 py-0.5 text-[11px]" : "px-3 py-1 text-xs",
        getStyle()
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-70" />
      {stage}
    </span>
  );
};

// Match Category Badge Component
export const FitScoreBadge: React.FC<{ score: number; category?: MatchCategory; showCategory?: boolean }> = ({
  score,
  category,
  showCategory = true
}) => {
  const getColor = () => {
    if (score >= 85) return 'text-emerald-800 bg-emerald-50/80 border-emerald-200';
    if (score >= 75) return 'text-coral-800 bg-coral-50/80 border-coral-200';
    if (score >= 60) return 'text-ochre-800 bg-ochre-50/80 border-ochre-200';
    return 'text-charcoal-600 bg-canvas-200 border-charcoal-300';
  };

  return (
    <div className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold shadow-2xs", getColor())}>
      <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
      <span>{score}% match</span>
      {showCategory && category && (
        <>
          <span className="opacity-40">•</span>
          <span className="font-medium">{category}</span>
        </>
      )}
    </div>
  );
};

// Empty State Component
export const EmptyState: React.FC<{
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}> = ({ icon, title, description, action }) => {
  return (
    <div className="py-12 px-4 text-center flex flex-col items-center justify-center">
      {icon && <div className="text-charcoal-400 mb-3">{icon}</div>}
      <h4 className="text-sm font-bold text-charcoal-900 mb-1">{title}</h4>
      <p className="text-xs text-charcoal-600 max-w-sm mb-4 leading-relaxed">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};

// Accessible Modal / Dialog Component
export const Modal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
  maxWidth?: string;
}> = ({ isOpen, onClose, title, subtitle, children, maxWidth = 'max-w-lg' }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/50 backdrop-blur-xs">
      <div className={cn("bg-white border border-charcoal-200/80 rounded-2xl shadow-dropdown w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200", maxWidth)}>
        <div className="px-6 py-4.5 border-b border-charcoal-100 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-charcoal-900 text-sm tracking-tight">{title}</h3>
            {subtitle && <p className="text-xs text-charcoal-500 mt-0.5">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="text-charcoal-400 hover:text-charcoal-700 p-1.5 rounded-lg hover:bg-canvas-100 transition-colors"
          >
            ✕
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};
