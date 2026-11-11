import React from 'react';
import { Link } from 'react-router-dom';
import {
  GraduationCap,
  ArrowRight,
  Briefcase,
  FileCheck,
  ShieldCheck,
  Compass
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#F5F6F4] text-slate-900 flex flex-col font-sans antialiased selection:bg-coral-500 selection:text-white">
      {/* 1. Cinematic Light Hero Section */}
      <section className="relative min-h-[90vh] flex flex-col justify-between overflow-hidden">
        {/* Real Non-AI Photography: Students collaborating around campus wooden table */}
        <div 
          className="absolute inset-0 bg-cover bg-[center_right] md:bg-center bg-no-repeat"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=2400&q=85')`
          }}
        />

        {/* Directional Overlay: Pulled to the left-middle so students and center background are clearly visible */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#FAF9F6] via-[#FAF9F6]/85 via-25% via-[#FAF9F6]/25 via-45% to-transparent pointer-events-none" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#FAF9F6] via-transparent to-transparent md:hidden pointer-events-none" />

        {/* Minimal Light Top Navigation */}
        <header className="relative z-20 max-w-7xl w-full mx-auto px-6 md:px-14 py-7 flex items-center justify-between">
          {/* Prominent NEXORA Brand Identity */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-sm bg-[#162232] text-white flex items-center justify-center font-bold shadow-sm border border-slate-700/30">
              <GraduationCap className="w-5 h-5 text-coral-400" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-display font-black text-2xl tracking-tight text-slate-900">
                  NEXORA
                </span>
                <span className="px-1.5 py-0.5 rounded-sm bg-coral-50 border border-coral-200/80 text-coral-700 font-mono text-[10px] font-bold uppercase tracking-wider">
                  Co-pilot
                </span>
              </div>
              <span className="text-[11px] text-slate-500 font-medium tracking-wide">
                Universal Career &amp; Placement Intelligence
              </span>
            </div>
          </div>

          <nav className="flex items-center gap-6 text-xs md:text-sm font-semibold tracking-wide">
            <a 
              href="#capabilities" 
              className="text-white hover:text-coral-400 transition-colors drop-shadow-md relative py-1 after:absolute after:bottom-0 after:left-0 after:w-full after:h-0.5 after:bg-coral-500"
            >
              Platform
            </a>
            <Link 
              to="/login" 
              className="px-4 py-2 rounded-md bg-white/20 hover:bg-white/30 text-white font-bold uppercase tracking-wider text-xs border border-white/50 backdrop-blur-md shadow-sm transition-all drop-shadow-sm"
            >
              Sign In
            </Link>
          </nav>
        </header>

        {/* Hero Content (Clean Left-Aligned Editorial + Floating Live Opportunity Badges on the Right) */}
        <div className="relative z-20 max-w-7xl w-full mx-auto px-6 md:px-14 py-12 md:py-16 flex-1 flex items-center justify-between">
          {/* Left Text Column: Seamlessly breathes on canvas with no clunky box */}
          <div className="max-w-xl space-y-6">
            {/* Nexora Eyebrow Pill */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/80 border border-slate-300/80 shadow-subtle text-[11px] font-mono font-semibold text-slate-700 backdrop-blur-sm">
              <span className="w-2 h-2 rounded-full bg-coral-500" />
              <span>NEXORA PLATFORM • OPEN TO STUDENTS FROM ANY COLLEGE</span>
            </div>

            {/* Modern Geometric Headline (Outfit / Plus Jakarta Sans) */}
            <h1 className="font-display text-4xl sm:text-5xl md:text-[50px] font-bold tracking-tight text-slate-900 leading-[1.12]">
              Your placement journey, <br />
              <span className="text-slate-700 font-semibold">organised and moving forward.</span>
            </h1>

            {/* Concise Value Subtitle */}
            <p className="text-sm sm:text-base text-slate-600 font-normal leading-relaxed max-w-lg">
              Designed for students from any college, university, or institute. Discover verified opportunities, tailor genuine application materials without fabricating claims, and practice with structured interview feedback.
            </p>

            {/* Sharp, Clean Action Buttons */}
            <div className="pt-2 flex flex-wrap items-center gap-4">
              <Link to="/signup">
                <button className="px-7 py-3.5 bg-coral-500 hover:bg-coral-600 text-white text-xs sm:text-sm font-bold uppercase tracking-wider rounded-md shadow-card hover:shadow-float transition-all flex items-center gap-2">
                  <span>Start My Plan</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </Link>
              <Link to="/login">
                <button className="px-7 py-3.5 bg-white/90 hover:bg-white text-slate-800 text-xs sm:text-sm font-bold uppercase tracking-wider rounded-md border border-slate-300 shadow-sm backdrop-blur-sm transition-all">
                  Sign In
                </button>
              </Link>
            </div>
          </div>

          {/* Right Column: Floating Live Co-pilot Intelligence Badges (Dribbble-style Cool Micro-UI) */}
          <div className="hidden lg:flex flex-col gap-4 max-w-xs w-full mr-4">
            {/* Badge 1: Verified Fit Score */}
            <div className="bg-white/90 backdrop-blur-md border border-white/90 rounded-xl p-4 shadow-[0_16px_36px_rgba(0,0,0,0.08)] transform hover:-translate-y-0.5 transition-transform duration-200">
              <div className="flex items-center justify-between mb-2">
                <span className="inline-flex items-center gap-1.5 text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Live Match
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                  94% Fit
                </span>
              </div>
              <p className="text-xs font-bold text-slate-900">Vercel • Software Engineer Intern</p>
              <p className="text-[11px] text-slate-500 mt-1">Matched with your React &amp; TypeScript skills</p>
            </div>

            {/* Badge 2: Scheduled Technical Round */}
            <div className="bg-white/90 backdrop-blur-md border border-white/90 rounded-xl p-4 shadow-[0_16px_36px_rgba(0,0,0,0.08)] ml-6 transform hover:-translate-y-0.5 transition-transform duration-200">
              <div className="flex items-center justify-between mb-2">
                <span className="inline-flex items-center gap-1.5 text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider">
                  <span className="w-2 h-2 rounded-full bg-ochre-500" />
                  Upcoming Round
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-ochre-50 text-ochre-800 border border-ochre-200 font-mono">
                  Nov 15
                </span>
              </div>
              <p className="text-xs font-bold text-slate-900">Stripe • Round 2 Systems</p>
              <p className="text-[11px] text-slate-500 mt-1">Concurrency &amp; Transactions</p>
            </div>
          </div>
        </div>

        {/* Bottom Hero Bar with Dot Indicator (Clean Right Alignment) */}
        <div className="relative z-20 max-w-7xl w-full mx-auto px-6 md:px-14 pb-8 flex items-center justify-end text-xs text-slate-600">
          {/* Reference-style Dot Indicators */}
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-coral-500" />
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
          </div>
        </div>
      </section>

      {/* 2. Core Capabilities Strip (Clean White Cards, rounded-md) */}
      <section id="capabilities" className="py-16 bg-[#F5F6F4] border-t border-slate-200 px-6 md:px-14">
        <div className="max-w-7xl mx-auto space-y-10">
          <div className="border-b border-slate-200 pb-5">
            <span className="text-[11px] font-mono font-bold text-coral-600 uppercase tracking-widest block mb-1">
              System Pillars
            </span>
            <h2 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Placement Architecture
            </h2>
          </div>

          {/* 4 Sharp Bordered Grid Blocks (Clean White Cards, rounded-md) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 01 */}
            <div className="bg-white border border-slate-200/90 rounded-md p-5 space-y-3 hover:border-coral-400 hover:shadow-subtle transition-all">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-coral-600">01</span>
                <Briefcase className="w-4 h-4 text-coral-600" />
              </div>
              <h3 className="font-bold text-sm text-slate-900">Fit-Scored Discovery</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Roles matched against confirmed skills with transparent fit scores and gap explanations.
              </p>
            </div>

            {/* 02 */}
            <div className="bg-white border border-slate-200/90 rounded-md p-5 space-y-3 hover:border-ochre-400 hover:shadow-subtle transition-all">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-ochre-600">02</span>
                <FileCheck className="w-4 h-4 text-ochre-600" />
              </div>
              <h3 className="font-bold text-sm text-slate-900">Truthful Resume Studio</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Tailor bullet points to job descriptions without fabricating fake achievements or numbers.
              </p>
            </div>

            {/* 03 */}
            <div className="bg-white border border-slate-200/90 rounded-md p-5 space-y-3 hover:border-emerald-400 hover:shadow-subtle transition-all">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-emerald-600">03</span>
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
              </div>
              <h3 className="font-bold text-sm text-slate-900">Student Sovereignty</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Nothing is submitted automatically. Every resume, letter, and note requires explicit sign-off.
              </p>
            </div>

            {/* 04 */}
            <div className="bg-white border border-slate-200/90 rounded-md p-5 space-y-3 hover:border-violet-400 hover:shadow-subtle transition-all">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-violet-600">04</span>
                <Compass className="w-4 h-4 text-violet-600" />
              </div>
              <h3 className="font-bold text-sm text-slate-900">Rubric Mock Prep</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Realistic technical interviews scored on standard rubrics that feed directly into your skill roadmap.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Action Banner */}
      <section className="py-14 bg-[#F5F6F4] border-t border-slate-200 px-6 md:px-14">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 bg-white border border-slate-200/90 rounded-md p-8 shadow-subtle">
          <div className="space-y-1 text-center md:text-left">
            <h3 className="font-display text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Ready to organise your placement season?
            </h3>
            <p className="text-xs sm:text-sm text-slate-600">
              Start with your baseline profile or sign in to continue your active pipeline.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link to="/login">
              <button className="px-6 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs sm:text-sm font-bold uppercase tracking-wider rounded-sm border border-slate-300 transition-all">
                Sign In
              </button>
            </Link>
            <Link to="/signup">
              <button className="px-6 py-2.5 bg-coral-500 hover:bg-coral-600 text-white text-xs sm:text-sm font-bold uppercase tracking-wider rounded-sm shadow-sm transition-all flex items-center gap-2">
                <span>Start</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </Link>
          </div>
        </div>
      </section>

      {/* 5. Clean Light Footer */}
      <footer className="py-6 px-6 md:px-14 bg-[#FAF9F6] border-t border-slate-200 text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <GraduationCap className="w-4 h-4 text-coral-500" />
          <span className="font-display font-bold text-slate-900">NEXORA</span>
          <span>© 2026</span>
          <span className="text-slate-400">•</span>
          <span>Placement &amp; Career Co-pilot</span>
        </div>
        <div className="flex items-center gap-6">
          <Link to="/login" className="hover:text-slate-900 transition-colors">Sign In</Link>
          <Link to="/signup" className="hover:text-slate-900 transition-colors">Create Account</Link>
        </div>
      </footer>
    </div>
  );
};
