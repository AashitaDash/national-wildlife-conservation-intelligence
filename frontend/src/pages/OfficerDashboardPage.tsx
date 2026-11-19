import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  Compass,
  AlertCircle,
  ExternalLink,
  Camera,
  MapPin,
  Calendar,
  Send,
  Eye,
  Check,
  X,
  MessageSquare,
  Bot,
  FileText,
  AlertOctagon,
  ShieldAlert,
  PlusCircle,
  FileCheck,
  DownloadCloud,
  ChevronRight
} from 'lucide-react';
import { officerService } from '../services/api';
import { Submission, OfficerQueueStats } from '../types';

export const OfficerDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<OfficerQueueStats | null>(null);
  const [queue, setQueue] = useState<Submission[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('PENDING_REVIEW');
  const [loading, setLoading] = useState<boolean>(true);

  // Selected item modal / active inspection
  const [activeSub, setActiveSub] = useState<Submission | null>(null);
  const [actionNote, setActionNote] = useState<string>('');
  const [submittingAction, setSubmittingAction] = useState<boolean>(false);
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsRes, queueRes] = await Promise.allSettled([
        officerService.getQueueStats(),
        officerService.getQueue({ status: filterStatus || undefined }),
      ]);
      if (statsRes.status === 'fulfilled') setStats(statsRes.value);
      if (queueRes.status === 'fulfilled') setQueue(queueRes.value);
    } catch (err) {
      console.error('Failed to load officer queue', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterStatus]);

  const handleClaim = async (subId: number) => {
    try {
      setSubmittingAction(true);
      setActionMsg(null);
      const updated = await officerService.claimSubmission(subId);
      setActionMsg({ type: 'success', text: `Claimed submission #${subId} under review.` });
      setActiveSub(updated);
      await loadData();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to claim.' });
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleVerify = async (subId: number) => {
    try {
      setSubmittingAction(true);
      setActionMsg(null);
      await officerService.verifySubmission(subId, actionNote || undefined);
      setActionMsg({
        type: 'success',
        text: `Submission #${subId} VERIFIED and promoted to National Wildlife Registry! Researcher awarded 50 points.`,
      });
      setActionNote('');
      setActiveSub(null);
      await loadData();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Verification failed.' });
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleReject = async (subId: number) => {
    if (!actionNote.trim()) {
      setActionMsg({ type: 'error', text: 'Please provide a clear justification for rejecting field evidence.' });
      return;
    }
    try {
      setSubmittingAction(true);
      setActionMsg(null);
      await officerService.rejectSubmission(subId, actionNote);
      setActionMsg({ type: 'success', text: `Submission #${subId} rejected.` });
      setActionNote('');
      setActiveSub(null);
      await loadData();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Rejection failed.' });
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleRequestInfo = async (subId: number) => {
    if (!actionNote.trim()) {
      setActionMsg({ type: 'error', text: 'Please specify the exact additional information or clearer evidence required.' });
      return;
    }
    try {
      setSubmittingAction(true);
      setActionMsg(null);
      await officerService.requestMoreInfo(subId, actionNote);
      setActionMsg({ type: 'success', text: `Revision requested from researcher for submission #${subId}.` });
      setActionNote('');
      setActiveSub(null);
      await loadData();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Request info failed.' });
    } finally {
      setSubmittingAction(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#e2ded5] pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold tracking-widest text-[#11682f] uppercase mb-1">
            <ShieldCheck className="w-4 h-4 text-[#11682f]" />
            Forest Department Verification Desk
          </div>
          <h1 className="text-3xl font-serif font-bold text-[#1f1e1a]">Forest Officer Command</h1>
          <p className="text-sm text-[#736f66] mt-1">
            Field-focused operational workspace: inspect incident alerts, audit submissions, navigate GIS spatial intel, and record field observations.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/submit"
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-[#11682f] hover:bg-[#0e5426] text-white text-xs font-mono font-bold tracking-wider uppercase rounded shadow-sm transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            Field Observation / Incident Report
          </Link>
          <Link
            to="/my-submissions"
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-[#faf9f6] border border-[#d6d2c7] text-[#2c2b27] text-xs font-mono font-bold tracking-wider uppercase rounded transition-colors"
          >
            <FileCheck className="w-4 h-4 text-[#11682f]" />
            Field Records
          </Link>
        </div>
      </div>

      {/* Mandatory Field Tools — AI Assistant & NLP / Ask the Corpus (Both Mandatory) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <Link
          to="/assistant"
          className="group p-4 rounded border border-[#e2ded5] bg-white shadow-sm hover:border-[#11682f] hover:shadow-md transition-all flex flex-col justify-between"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="w-8 h-8 rounded bg-[#11682f15] text-[#11682f] flex items-center justify-center group-hover:bg-[#11682f] group-hover:text-white transition-colors">
              <Bot className="w-4 h-4" />
            </div>
            <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-[#11682f]">Mandatory</span>
          </div>
          <div>
            <h4 className="font-serif font-bold text-sm text-[#1f1e1a]">AI Assistant</h4>
            <p className="text-[11px] text-[#736f66] mt-0.5 leading-snug">
              Operational RAG query assistant grounded in verified conservation data.
            </p>
          </div>
        </Link>

        <Link
          to="/documents"
          className="group p-4 rounded border border-[#e2ded5] bg-white shadow-sm hover:border-[#0891b2] hover:shadow-md transition-all flex flex-col justify-between"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="w-8 h-8 rounded bg-[#0891b215] text-[#0891b2] flex items-center justify-center group-hover:bg-[#0891b2] group-hover:text-white transition-colors">
              <FileText className="w-4 h-4" />
            </div>
            <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-[#0891b2]">Mandatory</span>
          </div>
          <div>
            <h4 className="font-serif font-bold text-sm text-[#1f1e1a]">NLP / Ask Corpus</h4>
            <p className="text-[11px] text-[#736f66] mt-0.5 leading-snug">
              Search patrol logs, incident dispatches, and conservation documents.
            </p>
          </div>
        </Link>

        <Link
          to="/map"
          className="group p-4 rounded border border-[#e2ded5] bg-white shadow-sm hover:border-[#16a34a] hover:shadow-md transition-all flex flex-col justify-between"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="w-8 h-8 rounded bg-[#16a34a15] text-[#16a34a] flex items-center justify-center group-hover:bg-[#16a34a] group-hover:text-white transition-colors">
              <MapPin className="w-4 h-4" />
            </div>
            <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-[#16a34a]">GIS</span>
          </div>
          <div>
            <h4 className="font-serif font-bold text-sm text-[#1f1e1a]">GIS Spatial Map</h4>
            <p className="text-[11px] text-[#736f66] mt-0.5 leading-snug">
              Inspect georeferenced sightings, patrol tracks, and sensitive coordinates.
            </p>
          </div>
        </Link>

        <Link
          to="/alerts"
          className="group p-4 rounded border border-[#e2ded5] bg-white shadow-sm hover:border-[#dc2626] hover:shadow-md transition-all flex flex-col justify-between"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="w-8 h-8 rounded bg-[#dc262615] text-[#dc2626] flex items-center justify-center group-hover:bg-[#dc2626] group-hover:text-white transition-colors">
              <AlertOctagon className="w-4 h-4" />
            </div>
            <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-[#dc2626]">Real-time</span>
          </div>
          <div>
            <h4 className="font-serif font-bold text-sm text-[#1f1e1a]">Threat Alerts</h4>
            <p className="text-[11px] text-[#736f66] mt-0.5 leading-snug">
              Poaching threats, human-wildlife conflict hotspots, and ML anomalies.
            </p>
          </div>
        </Link>
      </div>

      {/* Metrics Row */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="bg-white p-4 rounded border border-[#e2ded5] shadow-sm">
            <div className="text-xs font-mono text-[#736f66] uppercase tracking-wider mb-1">
              Pending Audit
            </div>
            <div className="text-2xl font-serif font-bold text-[#b07d1a]">
              {stats.pending_review}
            </div>
          </div>
          <div className="bg-white p-4 rounded border border-[#e2ded5] shadow-sm">
            <div className="text-xs font-mono text-[#736f66] uppercase tracking-wider mb-1">
              In Progress
            </div>
            <div className="text-2xl font-serif font-bold text-[#345280]">
              {stats.under_review}
            </div>
          </div>
          <div className="bg-white p-4 rounded border border-[#e2ded5] shadow-sm">
            <div className="text-xs font-mono text-[#736f66] uppercase tracking-wider mb-1">
              Needs Info
            </div>
            <div className="text-2xl font-serif font-bold text-[#8a5b00]">
              {stats.more_info_needed}
            </div>
          </div>
          <div className="bg-white p-4 rounded border border-[#e2ded5] shadow-sm">
            <div className="text-xs font-mono text-[#736f66] uppercase tracking-wider mb-1">
              Verified
            </div>
            <div className="text-2xl font-serif font-bold text-[#11682f]">
              {stats.verified}
            </div>
          </div>
          <div className="bg-white p-4 rounded border border-[#e2ded5] shadow-sm">
            <div className="text-xs font-mono text-[#736f66] uppercase tracking-wider mb-1">
              Total Audited
            </div>
            <div className="text-2xl font-serif font-bold text-[#1f1e1a]">
              {stats.total}
            </div>
          </div>
        </div>
      )}

      {actionMsg && (
        <div
          className={`p-3 rounded text-xs font-mono flex items-center gap-2 ${
            actionMsg.type === 'success'
              ? 'bg-[#e7f6ed] border border-[#b8e5c8] text-[#11682f]'
              : 'bg-[#fde8e7] border border-[#f5b8b5] text-[#932720]'
          }`}
        >
          {actionMsg.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0" />
          )}
          {actionMsg.text}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 border-b border-[#e2ded5] text-xs font-mono">
        {[
          { label: 'PENDING AUDIT', value: 'PENDING_REVIEW' },
          { label: 'UNDER REVIEW', value: 'UNDER_REVIEW' },
          { label: 'INFO REQUESTED', value: 'MORE_INFO_NEEDED' },
          { label: 'VERIFIED', value: 'VERIFIED' },
          { label: 'REJECTED', value: 'REJECTED' },
          { label: 'ALL LOGS', value: '' },
        ].map((tab) => (
          <button
            key={tab.value}
            onClick={() => setFilterStatus(tab.value)}
            className={`px-3 py-1.5 rounded-t font-semibold tracking-wider transition-colors uppercase ${
              filterStatus === tab.value
                ? 'bg-white border-t border-x border-[#e2ded5] text-[#11682f] shadow-sm'
                : 'text-[#736f66] hover:text-[#1f1e1a]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Verification Queue & Active Review Area */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Queue Table */}
        <div className="lg:col-span-7 bg-white rounded border border-[#e2ded5] shadow-sm overflow-hidden">
          <div className="p-4 border-b border-[#e2ded5] flex items-center justify-between">
            <h4 className="font-serif font-bold text-base text-[#1f1e1a]">Verification Queue</h4>
            <span className="font-mono text-xs text-[#736f66]">{queue.length} items</span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-xs font-mono text-[#736f66]">Loading verification queue...</div>
          ) : queue.length === 0 ? (
            <div className="p-8 text-center text-xs font-mono text-[#736f66]">
              Queue clear! No submissions awaiting verification under this filter.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[#e2ded5] bg-[#f9f8f5] text-[#736f66] font-mono uppercase tracking-wider">
                    <th className="py-2.5 px-3">Species</th>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Photos</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f0ede6]">
                  {queue.map((sub) => (
                    <tr
                      key={sub.id}
                      onClick={() => setActiveSub(sub)}
                      className={`cursor-pointer transition-colors ${
                        activeSub?.id === sub.id ? 'bg-[#d8f3e1]' : 'hover:bg-[#faf9f6]'
                      }`}
                    >
                      <td className="py-3 px-3">
                        <div className="font-semibold text-[#1f1e1a]">{sub.species_common_name}</div>
                        <div className="font-serif italic text-[#736f66] text-[11px]">
                          {sub.species_scientific_name}
                        </div>
                      </td>
                      <td className="py-3 px-3 font-mono text-[#736f66]">
                        {new Date(sub.observed_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-3 font-mono">
                        {sub.images && sub.images.length > 0 ? (
                          <span className="text-[#11682f] font-semibold">{sub.images.length}</span>
                        ) : (
                          <span className="text-[#a39e93]">0</span>
                        )}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold tracking-wider uppercase ${
                            sub.status === 'VERIFIED'
                              ? 'bg-[#d8f3e1] text-[#11682f]'
                              : sub.status === 'REJECTED'
                              ? 'bg-[#fde2e1] text-[#a8251e]'
                              : sub.status === 'MORE_INFO_NEEDED'
                              ? 'bg-[#fff1d0] text-[#8a5b00]'
                              : 'bg-[#edf1f7] text-[#345280]'
                          }`}
                        >
                          {sub.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right font-mono">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveSub(sub);
                          }}
                          className="text-[#11682f] hover:underline font-bold"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right: Inspection & Decision Cockpit */}
        <div className="lg:col-span-5 space-y-4">
          {activeSub ? (
            <div className="bg-white rounded border border-[#e2ded5] shadow-sm p-5 space-y-5">
              <div className="flex items-start justify-between border-b border-[#e2ded5] pb-3">
                <div>
                  <h3 className="font-serif font-bold text-lg text-[#1f1e1a]">
                    {activeSub.species_common_name}
                  </h3>
                  <p className="font-serif italic text-xs text-[#736f66]">
                    {activeSub.species_scientific_name}
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-mono uppercase text-[#736f66]">Audit Item</span>
                  <div className="font-mono font-bold text-sm text-[#2c2b27]">#{activeSub.id}</div>
                </div>
              </div>

              {/* Observation Metadata */}
              <div className="grid grid-cols-2 gap-3 bg-[#faf9f6] p-3 rounded border border-[#f0ede6] text-xs font-mono">
                <div>
                  <span className="text-[#736f66] block">Coordinates</span>
                  <span className="font-bold text-[#1f1e1a]">
                    {activeSub.latitude.toFixed(5)}, {activeSub.longitude.toFixed(5)}
                  </span>
                </div>
                <div>
                  <span className="text-[#736f66] block">Observed Time</span>
                  <span className="font-bold text-[#1f1e1a]">
                    {new Date(activeSub.observed_at).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Field Description */}
              <div>
                <span className="text-xs font-mono font-bold uppercase text-[#736f66] block mb-1">
                  Researcher Field Log
                </span>
                <p className="text-xs text-[#2c2b27] bg-[#faf9f6] p-3 rounded border border-[#f0ede6] leading-relaxed">
                  {activeSub.description}
                </p>
              </div>

              {/* Photos Gallery */}
              <div>
                <span className="text-xs font-mono font-bold uppercase text-[#736f66] block mb-2">
                  Photographic Evidence ({activeSub.images ? activeSub.images.length : 0})
                </span>
                {activeSub.images && activeSub.images.length > 0 ? (
                  <div className="grid grid-cols-2 gap-2">
                    {activeSub.images.map((img) => (
                      <div key={img.id} className="relative group rounded overflow-hidden border border-[#e2ded5] bg-[#1a1916]">
                        <img
                          src={`http://127.0.0.1:8000/${img.file_path}`}
                          alt="Field Evidence"
                          className="w-full h-32 object-cover"
                          onError={(e: any) => {
                            e.target.style.display = 'none';
                          }}
                        />
                        <div className="p-1.5 text-[9px] font-mono text-[#a39e93] truncate bg-[#1a1916]">
                          {img.original_filename || 'Evidence Photo'}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-3 bg-[#faf9f6] border border-[#f0ede6] rounded text-xs text-[#a39e93] font-mono">
                    No photographic evidence attached to this sighting.
                  </div>
                )}
              </div>

              {/* Officer Decision Box */}
              <div className="pt-4 border-t border-[#e2ded5] space-y-3">
                <label className="block text-xs font-mono font-bold uppercase text-[#4d4a43]">
                  Decision Note / Verification Justification:
                </label>
                <textarea
                  rows={3}
                  value={actionNote}
                  onChange={(e) => setActionNote(e.target.value)}
                  placeholder="e.g. Diagnostic stripe pattern aligns with Panthera tigris. Verified for inclusion."
                  className="w-full p-2.5 text-xs border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
                />

                {/* State-dependent buttons */}
                {activeSub.status === 'PENDING_REVIEW' && (
                  <button
                    disabled={submittingAction}
                    onClick={() => handleClaim(activeSub.id)}
                    className="w-full py-2 bg-[#345280] hover:bg-[#284166] text-white text-xs font-mono font-bold uppercase tracking-wider rounded transition-colors disabled:opacity-50"
                  >
                    Claim for Formal Review
                  </button>
                )}

                {(activeSub.status === 'UNDER_REVIEW' || activeSub.status === 'PENDING_REVIEW') && (
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      disabled={submittingAction}
                      onClick={() => handleVerify(activeSub.id)}
                      className="py-2.5 bg-[#11682f] hover:bg-[#0e5426] text-white text-xs font-mono font-bold uppercase tracking-wider rounded transition-colors disabled:opacity-50 flex items-center justify-center gap-1"
                    >
                      <Check className="w-3.5 h-3.5" /> Verify
                    </button>
                    <button
                      disabled={submittingAction}
                      onClick={() => handleRequestInfo(activeSub.id)}
                      className="py-2.5 bg-[#8a5b00] hover:bg-[#6e4900] text-white text-xs font-mono font-bold uppercase tracking-wider rounded transition-colors disabled:opacity-50 flex items-center justify-center gap-1"
                    >
                      <HelpCircle className="w-3.5 h-3.5" /> Need Info
                    </button>
                    <button
                      disabled={submittingAction}
                      onClick={() => handleReject(activeSub.id)}
                      className="py-2.5 bg-[#932720] hover:bg-[#781f19] text-white text-xs font-mono font-bold uppercase tracking-wider rounded transition-colors disabled:opacity-50 flex items-center justify-center gap-1"
                    >
                      <X className="w-3.5 h-3.5" /> Reject
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white p-12 rounded border border-[#e2ded5] text-center text-xs font-mono text-[#736f66]">
              Select a queue item from the table to inspect field evidence and issue official decision.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
