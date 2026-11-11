import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Send,
  Mail,
  Clock,
  Eye,
  ShieldCheck,
  Edit2
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, Button, Modal } from '../../components/common/UIComponents';
import type { FollowUpItem } from '../../types';

export const FollowUpAssistantPage: React.FC = () => {
  const navigate = useNavigate();
  const { followUps, saveFollowUpDraft, requestFollowUpApproval } = useApp();

  const [inspectItem, setInspectItem] = useState<FollowUpItem | null>(null);
  const [editingItem, setEditingItem] = useState<FollowUpItem | null>(null);

  const handleSaveEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingItem) return;
    saveFollowUpDraft(editingItem);
    setEditingItem(null);
  };

  const handleRequestApproval = (id: string) => {
    requestFollowUpApproval(id);
    navigate('/app/approvals');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Follow-up Assistant</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-800 border border-blue-200">
              Professional Communications
            </span>
          </div>
          <p className="text-xs text-charcoal-600 mt-1 max-w-2xl leading-relaxed">
            Timely, respectful recruiter follow-ups for post-interview acknowledgements and status inquiries.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/app/approvals">
            <Button variant="outline" size="sm">
              Approval Centre →
            </Button>
          </Link>
        </div>
      </div>

      {/* Follow-ups List */}
      <div className="space-y-4">
        {followUps.map((fu) => (
          <Panel key={fu.id} className="p-5 bg-white">
            <div className="flex flex-col md:flex-row items-start justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div className="w-9 h-9 rounded-md bg-steel-100 text-steel-700 flex items-center justify-center shrink-0">
                  <Mail className="w-4 h-4" />
                </div>

                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-bold text-sm text-charcoal-900">{fu.company}</h3>
                    <span className="text-charcoal-300">•</span>
                    <span className="text-xs text-charcoal-700">{fu.role}</span>
                    {fu.status === 'awaiting_approval' ? (
                      <span className="text-[10px] font-semibold text-purple-800 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                        Queued in Approval Centre
                      </span>
                    ) : (
                      <span className="text-[10px] font-semibold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                        Draft in Progress
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-charcoal-600 mt-1">
                    To: <span className="font-semibold text-charcoal-800">{fu.recipientName}</span> ({fu.recipientEmail})
                  </p>

                  <div className="mt-2 p-2.5 bg-canvas-50 border border-charcoal-200 rounded text-xs text-charcoal-800 font-mono text-[11px]">
                    <span className="font-bold text-charcoal-600">Subject: </span>{fu.subject}
                  </div>

                  <div className="mt-2 text-[11px] text-charcoal-600 flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5 text-steel-600" />
                    <span>Trigger: {fu.triggerReason} (Suggested Date: {fu.suggestedDate})</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 w-full md:w-auto shrink-0 justify-end">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setInspectItem(fu)}
                  icon={<Eye className="w-3.5 h-3.5" />}
                >
                  Preview Message
                </Button>

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setEditingItem(fu)}
                  icon={<Edit2 className="w-3.5 h-3.5" />}
                >
                  Edit Draft
                </Button>

                {fu.status === 'draft' && (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleRequestApproval(fu.id)}
                    icon={<Send className="w-3.5 h-3.5" />}
                  >
                    Send to Approvals
                  </Button>
                )}
              </div>
            </div>
          </Panel>
        ))}
      </div>

      {/* Modal: Preview Message */}
      {inspectItem && (
        <Modal
          isOpen={!!inspectItem}
          onClose={() => setInspectItem(null)}
          title={`Follow-up Preview: ${inspectItem.company}`}
          subtitle={`Subject: ${inspectItem.subject}`}
          maxWidth="max-w-xl"
        >
          <div className="space-y-4 text-xs">
            <div className="p-4 bg-canvas-50 border border-charcoal-200 rounded-md font-sans text-charcoal-900 leading-relaxed whitespace-pre-wrap">
              {inspectItem.message}
            </div>

            <div className="p-3 bg-steel-50 border border-steel-200 rounded text-[11px] text-steel-800 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-steel-600 shrink-0" />
              <span>Nexora never sends automated emails directly. Approving this message prepares it for you to send or export.</span>
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="outline" size="sm" onClick={() => setInspectItem(null)}>
                Close Preview
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: Edit Follow-up */}
      {editingItem && (
        <Modal
          isOpen={!!editingItem}
          onClose={() => setEditingItem(null)}
          title={`Edit Follow-up Message for ${editingItem.company}`}
          maxWidth="max-w-xl"
        >
          <form onSubmit={handleSaveEdit} className="space-y-3.5 text-xs">
            <div>
              <label className="block font-semibold text-charcoal-800 mb-1">Subject Line</label>
              <input
                type="text"
                required
                value={editingItem.subject}
                onChange={(e) => setEditingItem({ ...editingItem, subject: e.target.value })}
                className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
              />
            </div>

            <div>
              <label className="block font-semibold text-charcoal-800 mb-1">Email Body</label>
              <textarea
                rows={6}
                required
                value={editingItem.message}
                onChange={(e) => setEditingItem({ ...editingItem, message: e.target.value })}
                className="w-full bg-white border border-charcoal-200 rounded p-2.5 text-charcoal-900 leading-relaxed font-sans"
              />
            </div>

            <div className="pt-3 border-t border-charcoal-100 flex justify-end gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setEditingItem(null)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm">
                Save Changes
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
