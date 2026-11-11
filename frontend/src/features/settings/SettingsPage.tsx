import React, { useState } from 'react';
import {
  Save,
  CheckCircle2,
  Calendar,
  Globe
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, PanelHeader, PanelBody, Button } from '../../components/common/UIComponents';

export const SettingsPage: React.FC = () => {
  const { profile, updateProfile } = useApp();

  const [activeTab, setActiveTab] = useState<'account' | 'preferences' | 'privacy' | 'integrations'>('account');
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Settings states
  const [fullName, setFullName] = useState(profile.fullName);
  const [email, setEmail] = useState(profile.email);
  const [phone, setPhone] = useState(profile.phone);

  const [notifyDeadlines, setNotifyDeadlines] = useState(true);
  const [notifyApprovals, setNotifyApprovals] = useState(true);
  const [notifyMatches, setNotifyMatches] = useState(true);

  const handleSave = () => {
    updateProfile({
      fullName,
      email,
      phone
    });
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Platform Settings</h2>
          <p className="text-xs text-charcoal-600 mt-1">
            Configure your account preferences, notification alerts, and placement workflow controls.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {saveSuccess && (
            <span className="text-xs text-emerald-700 font-medium flex items-center gap-1 animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Preferences saved
            </span>
          )}
          <Button variant="primary" size="sm" onClick={handleSave} icon={<Save className="w-3.5 h-3.5" />}>
            Save Preferences
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto text-xs font-medium border-b border-charcoal-200 pb-2">
        <button
          onClick={() => setActiveTab('account')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            activeTab === 'account' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Account & Security
        </button>
        <button
          onClick={() => setActiveTab('preferences')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            activeTab === 'preferences' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Notifications
        </button>
        <button
          onClick={() => setActiveTab('privacy')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            activeTab === 'privacy' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Privacy & Data Controls
        </button>
        <button
          onClick={() => setActiveTab('integrations')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            activeTab === 'integrations' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Future Integrations
        </button>
      </div>

      {/* Account Tab */}
      {activeTab === 'account' && (
        <Panel>
          <PanelHeader title="Account Details" subtitle="Primary credentials and college verification" />
          <PanelBody className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-charcoal-700 mb-1">Full Legal Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
                />
              </div>

              <div>
                <label className="block font-semibold text-charcoal-700 mb-1">College Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
                />
              </div>

              <div>
                <label className="block font-semibold text-charcoal-700 mb-1">Contact Phone</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
                />
              </div>
            </div>

            <div className="pt-4 border-t border-charcoal-100">
              <h4 className="font-bold text-charcoal-900 text-xs mb-2">Change Password</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] text-charcoal-600 mb-1">Current Password</label>
                  <input
                    type="password"
                    placeholder="••••••••••••"
                    className="w-full bg-white border border-charcoal-200 rounded p-1.5 text-xs text-charcoal-900"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-charcoal-600 mb-1">New Password</label>
                  <input
                    type="password"
                    placeholder="••••••••••••"
                    className="w-full bg-white border border-charcoal-200 rounded p-1.5 text-xs text-charcoal-900"
                  />
                </div>
              </div>
            </div>
          </PanelBody>
        </Panel>
      )}

      {/* Preferences / Notifications Tab */}
      {activeTab === 'preferences' && (
        <Panel>
          <PanelHeader title="Notification & Alert Thresholds" />
          <PanelBody className="space-y-4 text-xs">
            <label className="flex items-start gap-3 p-3 bg-canvas-50 border border-charcoal-200 rounded cursor-pointer">
              <input
                type="checkbox"
                checked={notifyDeadlines}
                onChange={(e) => setNotifyDeadlines(e.target.checked)}
                className="mt-0.5 rounded border-charcoal-300 text-navy-800"
              />
              <div>
                <span className="font-bold text-charcoal-900 block">Upcoming Deadlines & Coding Assessments</span>
                <span className="text-[11px] text-charcoal-600">
                  Notify 24 hours prior to application close or assessment expiry.
                </span>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3 bg-canvas-50 border border-charcoal-200 rounded cursor-pointer">
              <input
                type="checkbox"
                checked={notifyApprovals}
                onChange={(e) => setNotifyApprovals(e.target.checked)}
                className="mt-0.5 rounded border-charcoal-300 text-navy-800"
              />
              <div>
                <span className="font-bold text-charcoal-900 block">Pending Document Approvals</span>
                <span className="text-[11px] text-charcoal-600">
                  Remind when a tailored resume or cover letter draft is queued in the Approval Centre.
                </span>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3 bg-canvas-50 border border-charcoal-200 rounded cursor-pointer">
              <input
                type="checkbox"
                checked={notifyMatches}
                onChange={(e) => setNotifyMatches(e.target.checked)}
                className="mt-0.5 rounded border-charcoal-300 text-navy-800"
              />
              <div>
                <span className="font-bold text-charcoal-900 block">High-Fit Opportunity Matches (&gt;85%)</span>
                <span className="text-[11px] text-charcoal-600">
                  Surface alerts when new postings align with your confirmed skill profile.
                </span>
              </div>
            </label>
          </PanelBody>
        </Panel>
      )}

      {/* Privacy Tab */}
      {activeTab === 'privacy' && (
        <Panel>
          <PanelHeader title="Privacy, Sovereignty & Student Data Controls" />
          <PanelBody className="space-y-4 text-xs">
            <div className="p-4 bg-steel-50 border border-steel-200 rounded text-steel-950 space-y-1">
              <span className="font-bold text-xs block">Student Data Isolation Guarantee</span>
              <p className="text-[11px] leading-relaxed">
                Your resume, interview transcripts, and customized drafts remain private to your student session. Nexora does not use your real personal projects to train shared models or share draft materials without approval.
              </p>
            </div>

            <div className="pt-2 space-y-3">
              <div className="flex items-center justify-between p-3 border border-charcoal-200 rounded">
                <div>
                  <span className="font-bold text-charcoal-900 block">Export Placement Data</span>
                  <span className="text-[11px] text-charcoal-600">Download all applications, tailored resumes, and feedback logs as JSON.</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => alert('Placement data export prepared.')}
                >
                  Export Data
                </Button>
              </div>
            </div>
          </PanelBody>
        </Panel>
      )}

      {/* Integrations Tab */}
      {activeTab === 'integrations' && (
        <Panel>
          <PanelHeader title="External Platform Integrations" subtitle="Future backend integration boundaries" />
          <PanelBody className="space-y-3 text-xs">
            <div className="p-4 border border-charcoal-200 rounded flex items-center justify-between bg-white">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-canvas-100 flex items-center justify-center text-charcoal-700">
                  <Calendar className="w-4 h-4" />
                </div>
                <div>
                  <span className="font-bold text-charcoal-900 block">Google Calendar / Outlook Sync</span>
                  <span className="text-[11px] text-charcoal-600">Auto-sync interview dates and coding assessment deadlines.</span>
                </div>
              </div>
              <span className="px-2.5 py-1 bg-canvas-100 text-charcoal-600 rounded text-[11px] font-semibold border border-charcoal-200">
                Future Integration Phase
              </span>
            </div>

            <div className="p-4 border border-charcoal-200 rounded flex items-center justify-between bg-white">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-canvas-100 flex items-center justify-center text-charcoal-700">
                  <Globe className="w-4 h-4" />
                </div>
                <div>
                  <span className="font-bold text-charcoal-900 block">University &amp; College Placement Cell API (Superset / ERP / Handshake)</span>
                  <span className="text-[11px] text-charcoal-600">Connect institutional drive schedules, university portals, or open off-campus hiring.</span>
                </div>
              </div>
              <span className="px-2.5 py-1 bg-canvas-100 text-charcoal-600 rounded text-[11px] font-semibold border border-charcoal-200">
                Future Integration Phase
              </span>
            </div>
          </PanelBody>
        </Panel>
      )}
    </div>
  );
};
