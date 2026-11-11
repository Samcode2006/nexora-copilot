import React, { useState } from 'react';
import {
  CheckSquare,
  AlertCircle,
  FileText,
  Mail,
  Send,
  CheckCircle2,
  XCircle,
  Eye
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, Button, Modal } from '../../components/common/UIComponents';
import type { ApprovalItem } from '../../types';

export const ApprovalCentrePage: React.FC = () => {
  const { approvals, approveItem, rejectItem } = useApp();

  const [inspectItem, setInspectItem] = useState<ApprovalItem | null>(null);
  const [confirmApproveId, setConfirmApproveId] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('all');

  const pendingCount = approvals.filter(a => a.status === 'pending').length;

  const filteredApprovals = approvals.filter(item => {
    if (filterType === 'all') return true;
    if (filterType === 'pending') return item.status === 'pending';
    if (filterType === 'approved') return item.status === 'approved';
    return item.type === filterType;
  });

  const handleApprove = (id: string) => {
    approveItem(id);
    setConfirmApproveId(null);
    if (inspectItem && inspectItem.id === id) {
      setInspectItem({ ...inspectItem, status: 'approved' });
    }
  };

  const handleReject = (id: string) => {
    rejectItem(id);
    if (inspectItem && inspectItem.id === id) {
      setInspectItem({ ...inspectItem, status: 'rejected' });
    }
  };

  const getItemIcon = (type: ApprovalItem['type']) => {
    switch (type) {
      case 'tailored_resume':
        return <FileText className="w-4 h-4 text-purple-600" />;
      case 'cover_letter':
        return <Mail className="w-4 h-4 text-blue-600" />;
      case 'follow_up':
        return <Send className="w-4 h-4 text-steel-600" />;
      default:
        return <CheckSquare className="w-4 h-4 text-charcoal-600" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Approval Centre</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
              Student Sovereignty & Control
            </span>
          </div>
          <p className="text-xs text-charcoal-600 mt-1 max-w-2xl leading-relaxed">
            Nexora will never submit job applications or send messages on your behalf without your explicit student review and authorization.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-3 py-1.5 bg-canvas-100 border border-charcoal-200 rounded text-xs font-semibold text-charcoal-800">
            {pendingCount} Pending Review
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto text-xs font-medium border-b border-charcoal-200 pb-2">
        <button
          onClick={() => setFilterType('all')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            filterType === 'all' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          All Items ({approvals.length})
        </button>
        <button
          onClick={() => setFilterType('pending')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            filterType === 'pending' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Pending Only ({pendingCount})
        </button>
        <button
          onClick={() => setFilterType('tailored_resume')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            filterType === 'tailored_resume' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Tailored Resumes
        </button>
        <button
          onClick={() => setFilterType('cover_letter')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            filterType === 'cover_letter' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Cover Letters
        </button>
        <button
          onClick={() => setFilterType('follow_up')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            filterType === 'follow_up' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Follow-ups
        </button>
      </div>

      {/* Approvals List */}
      <div className="space-y-4">
        {filteredApprovals.map((item) => (
          <Panel key={item.id} className="p-5 bg-white">
            <div className="flex flex-col md:flex-row items-start justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div className="w-9 h-9 rounded-md bg-canvas-100 border border-charcoal-200 flex items-center justify-center shrink-0">
                  {getItemIcon(item.type)}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-bold text-sm text-charcoal-900">{item.title}</h3>
                    <span className="text-[10px] uppercase font-bold text-charcoal-600 bg-canvas-100 px-2 py-0.5 rounded border border-charcoal-200">
                      {item.type.replace('_', ' ')}
                    </span>
                    {item.status === 'pending' && (
                      <span className="text-[10px] font-semibold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                        Awaiting Your Review
                      </span>
                    )}
                    {item.status === 'approved' && (
                      <span className="text-[10px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        Approved by Student
                      </span>
                    )}
                    {item.status === 'rejected' && (
                      <span className="text-[10px] font-semibold text-red-800 bg-red-50 px-2 py-0.5 rounded border border-red-200">
                        Rejected
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-charcoal-600 mt-1">
                    Related to: <span className="font-semibold text-charcoal-800">{item.company}</span> — {item.jobTitle}
                  </p>

                  <p className="text-xs text-charcoal-700 mt-2 bg-canvas-50 p-2.5 rounded border border-charcoal-200 leading-relaxed">
                    {item.summary}
                  </p>

                  {item.unverifiedWarnings.length > 0 && (
                    <div className="mt-2.5 flex items-start gap-1.5 text-xs text-amber-900 bg-amber-50/70 p-2 rounded border border-amber-200">
                      <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                      <span>{item.unverifiedWarnings[0]}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex flex-wrap items-center gap-2 w-full md:w-auto shrink-0 mt-2 md:mt-0 justify-end">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setInspectItem(item)}
                  icon={<Eye className="w-3.5 h-3.5" />}
                >
                  Inspect Content
                </Button>

                {item.status === 'pending' && (
                  <>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleReject(item.id)}
                      icon={<XCircle className="w-3.5 h-3.5" />}
                    >
                      Reject
                    </Button>

                    <Button
                      variant="success"
                      size="sm"
                      onClick={() => setConfirmApproveId(item.id)}
                      icon={<CheckCircle2 className="w-3.5 h-3.5" />}
                    >
                      Authorize & Approve
                    </Button>
                  </>
                )}
              </div>
            </div>
          </Panel>
        ))}

        {filteredApprovals.length === 0 && (
          <Panel className="p-8 text-center text-xs text-charcoal-600">
            No approval requests matching this filter.
          </Panel>
        )}
      </div>

      {/* Modal: Detailed Content Inspection */}
      {inspectItem && (
        <Modal
          isOpen={!!inspectItem}
          onClose={() => setInspectItem(null)}
          title={`Inspect: ${inspectItem.title}`}
          subtitle={`Company: ${inspectItem.company} • Status: ${inspectItem.status.toUpperCase()}`}
          maxWidth="max-w-2xl"
        >
          <div className="space-y-4 text-xs">
            {inspectItem.contentPreview.beforeText && (
              <div>
                <h4 className="font-semibold text-charcoal-700 text-[11px] uppercase mb-1">
                  Original Master Profile Baseline:
                </h4>
                <p className="p-2.5 bg-canvas-50 border border-charcoal-200 rounded text-charcoal-700 italic">
                  "{inspectItem.contentPreview.beforeText}"
                </p>
              </div>
            )}

            <div>
              <h4 className="font-semibold text-charcoal-700 text-[11px] uppercase mb-1">
                Generated / Tailored Content for Review:
              </h4>
              <p className="p-3 bg-white border border-charcoal-300 rounded font-medium text-charcoal-900 leading-relaxed whitespace-pre-wrap">
                {inspectItem.contentPreview.afterText}
              </p>
            </div>

            {inspectItem.contentPreview.highlights && (
              <div>
                <h4 className="font-semibold text-charcoal-700 text-[11px] uppercase mb-1">
                  Key Verification Tokens:
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {inspectItem.contentPreview.highlights.map(h => (
                    <span key={h} className="px-2 py-0.5 bg-steel-50 text-steel-700 border border-steel-200 rounded text-[11px] font-medium">
                      {h}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-4 border-t border-charcoal-100 flex items-center justify-between">
              <div className="text-[11px] text-charcoal-600">
                Approving places this verified packet into your Application Tracker.
              </div>
              <div className="flex items-center gap-2">
                {inspectItem.status === 'pending' ? (
                  <>
                    <Button variant="danger" size="sm" onClick={() => handleReject(inspectItem.id)}>
                      Reject
                    </Button>
                    <Button variant="success" size="sm" onClick={() => handleApprove(inspectItem.id)}>
                      Authorize & Approve
                    </Button>
                  </>
                ) : (
                  <Button variant="outline" size="sm" onClick={() => setInspectItem(null)}>
                    Close
                  </Button>
                )}
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: Confirmation for Approval */}
      {confirmApproveId && (
        <Modal
          isOpen={!!confirmApproveId}
          onClose={() => setConfirmApproveId(null)}
          title="Confirm Student Authorization"
          maxWidth="max-w-md"
        >
          <div className="space-y-4 text-xs">
            <div className="p-3 bg-amber-50 border border-amber-200 rounded text-amber-900">
              <p className="font-semibold mb-1">You are explicitly authorizing this document.</p>
              <p className="text-[11px]">
                By approving, you confirm that all highlighted achievements and skills accurately reflect your real work. The application stage will advance to <strong>"Ready to apply"</strong>.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setConfirmApproveId(null)}>
                Cancel
              </Button>
              <Button variant="success" size="sm" onClick={() => handleApprove(confirmApproveId)}>
                Confirm & Authorize
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
