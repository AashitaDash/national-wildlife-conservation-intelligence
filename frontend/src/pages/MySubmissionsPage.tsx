import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Plus,
  Send,
  Trash2,
  Camera,
  MapPin,
  Calendar,
} from 'lucide-react';
import { submissionService } from '../services/api';
import { Submission, SubmissionStatus } from '../types';

export const MySubmissionsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialStatus = searchParams.get('status') || '';

  const [statusFilter, setStatusFilter] = useState<string>(initialStatus);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedSub, setSelectedSub] = useState<Submission | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const loadSubmissions = async () => {
    try {
      setLoading(true);
      const data = await submissionService.getMySubmissions(statusFilter || undefined);
      setSubmissions(data);
      if (data.length > 0 && !selectedSub) {
        setSelectedSub(data[0]);
      }
    } catch (err) {
      console.error('Failed to load submissions', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubmissions();
  }, [statusFilter]);

  const handleFilterChange = (status: string) => {
    setStatusFilter(status);
    if (status) {
      setSearchParams({ status });
    } else {
      setSearchParams({});
    }
  };

  const handleSubmitDraft = async (id: number) => {
    try {
      setActionError(null);
      await submissionService.submitForReview(id);
      setActionSuccess('Submission transitioned to PENDING_REVIEW!');
      await loadSubmissions();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to submit draft.');
    }
  };

  const handleDeleteDraft = async (id: number) => {
    if (!window.confirm('Delete this draft permanently?')) return;
    try {
      setActionError(null);
      await submissionService.deleteDraft(id);
      setActionSuccess('Draft deleted.');
      setSelectedSub(null);
      await loadSubmissions();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to delete draft.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#e2ded5] pb-4">
        <div>
          <div className="text-xs font-mono font-bold tracking-widest text-[#11682f] uppercase mb-1">
            Field Records
          </div>
          <h1 className="text-2xl font-serif font-bold text-[#1f1e1a]">My Wildlife Submissions</h1>
        </div>
        <Link
          to="/submit"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#11682f] hover:bg-[#0e5426] text-white text-xs font-mono font-bold tracking-wider uppercase rounded transition-colors"
        >
          <Plus className="w-4 h-4" /> Log Sighting
        </Link>
      </div>

      {actionError && (
        <div className="p-3 bg-[#fde8e7] border border-[#f5b8b5] text-[#932720] text-xs font-mono rounded flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {actionError}
        </div>
      )}

      {actionSuccess && (
        <div className="p-3 bg-[#e7f6ed] border border-[#b8e5c8] text-[#11682f] text-xs font-mono rounded flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          {actionSuccess}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 border-b border-[#e2ded5] text-xs font-mono">
        {[
          { label: 'ALL SIGHTINGS', value: '' },
          { label: 'DRAFTS', value: 'DRAFT' },
          { label: 'IN REVIEW', value: 'PENDING_REVIEW' },
          { label: 'REVISIONS NEEDED', value: 'MORE_INFO_NEEDED' },
          { label: 'VERIFIED', value: 'VERIFIED' },
          { label: 'REJECTED', value: 'REJECTED' },
        ].map((tab) => (
          <button
            key={tab.value}
            onClick={() => handleFilterChange(tab.value)}
            className={`px-3 py-1.5 rounded-t font-semibold tracking-wider transition-colors uppercase ${
              statusFilter === tab.value
                ? 'bg-white border-t border-x border-[#e2ded5] text-[#11682f] shadow-sm'
                : 'text-[#736f66] hover:text-[#1f1e1a]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Two Column Layout: List & Detail View */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Left Column: Sighting List */}
        <div className="md:col-span-5 space-y-3">
          {loading ? (
            <div className="p-8 text-center text-xs font-mono text-[#736f66]">Loading sightings...</div>
          ) : submissions.length === 0 ? (
            <div className="bg-white p-8 rounded border border-[#e2ded5] text-center text-xs text-[#736f66]">
              No sightings found matching filter.
            </div>
          ) : (
            submissions.map((sub) => (
              <div
                key={sub.id}
                onClick={() => setSelectedSub(sub)}
                className={`p-4 rounded border cursor-pointer transition-all ${
                  selectedSub?.id === sub.id
                    ? 'bg-white border-[#11682f] shadow-md ring-1 ring-[#11682f]'
                    : 'bg-white border-[#e2ded5] hover:border-[#b0ab9f]'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div>
                    <h4 className="font-semibold text-sm text-[#1f1e1a]">
                      {sub.species_common_name || 'Unidentified Species'}
                    </h4>
                    <span className="font-serif italic text-xs text-[#736f66]">
                      {sub.species_scientific_name}
                    </span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider uppercase ${
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
                </div>
                <div className="flex items-center gap-4 text-[11px] font-mono text-[#736f66] mt-2">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {new Date(sub.observed_at).toLocaleDateString()}
                  </span>
                  <span className="flex items-center gap-1">
                    <Camera className="w-3 h-3" />
                    {sub.images ? sub.images.length : 0} photos
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Right Column: Detailed View */}
        <div className="md:col-span-7">
          {selectedSub ? (
            <div className="bg-white rounded border border-[#e2ded5] shadow-sm p-6 space-y-6">
              <div className="flex items-start justify-between border-b border-[#e2ded5] pb-4">
                <div>
                  <h3 className="text-xl font-serif font-bold text-[#1f1e1a]">
                    {selectedSub.species_common_name}
                  </h3>
                  <p className="font-serif italic text-sm text-[#736f66]">
                    {selectedSub.species_scientific_name}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-mono uppercase text-[#736f66]">Submission ID</div>
                  <div className="font-mono font-bold text-sm text-[#2c2b27]">#{selectedSub.id}</div>
                </div>
              </div>

              {/* Status Banner / Feedback */}
              {selectedSub.status === 'MORE_INFO_NEEDED' && (
                <div className="p-4 bg-[#fff9ed] border border-[#f0c36d] rounded space-y-2">
                  <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase text-[#8a5b00]">
                    <AlertCircle className="w-4 h-4" />
                    Officer Revision Request
                  </div>
                  <p className="text-xs text-[#4d3a0e] leading-relaxed">
                    {selectedSub.latest_decision?.note ||
                      'Please provide clearer dorsal markings or additional field habitat details.'}
                  </p>
                  <button
                    onClick={() => handleSubmitDraft(selectedSub.id)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#8a5b00] hover:bg-[#6e4900] text-white text-xs font-mono font-bold uppercase rounded"
                  >
                    <Send className="w-3.5 h-3.5" /> Re-submit to Officer
                  </button>
                </div>
              )}

              {/* Spatiotemporal Coordinates */}
              <div className="grid grid-cols-2 gap-4 bg-[#faf9f6] p-4 rounded border border-[#f0ede6] text-xs font-mono">
                <div>
                  <span className="text-[#736f66] block">Coordinates</span>
                  <span className="font-bold text-[#1f1e1a]">
                    {selectedSub.latitude.toFixed(6)}, {selectedSub.longitude.toFixed(6)}
                  </span>
                </div>
                <div>
                  <span className="text-[#736f66] block">Observed Timestamp</span>
                  <span className="font-bold text-[#1f1e1a]">
                    {new Date(selectedSub.observed_at).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Field Description */}
              <div className="space-y-1.5">
                <h5 className="font-mono text-xs font-bold uppercase text-[#736f66]">Field Description</h5>
                <p className="text-sm text-[#2c2b27] leading-relaxed bg-[#faf9f6] p-3 rounded border border-[#f0ede6]">
                  {selectedSub.description}
                </p>
              </div>

              {/* Optional Field Clues */}
              {(selectedSub.habitat_notes || selectedSub.behavior_notes || selectedSub.identification_notes) && (
                <div className="space-y-2 text-xs border-t border-[#f0ede6] pt-4">
                  {selectedSub.habitat_notes && (
                    <div>
                      <span className="font-mono font-bold text-[#736f66] uppercase">Habitat: </span>
                      <span className="text-[#2c2b27]">{selectedSub.habitat_notes}</span>
                    </div>
                  )}
                  {selectedSub.behavior_notes && (
                    <div>
                      <span className="font-mono font-bold text-[#736f66] uppercase">Behavior: </span>
                      <span className="text-[#2c2b27]">{selectedSub.behavior_notes}</span>
                    </div>
                  )}
                  {selectedSub.identification_notes && (
                    <div>
                      <span className="font-mono font-bold text-[#736f66] uppercase">Clues: </span>
                      <span className="text-[#2c2b27]">{selectedSub.identification_notes}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Photos */}
              <div className="space-y-2 border-t border-[#f0ede6] pt-4">
                <h5 className="font-mono text-xs font-bold uppercase text-[#736f66]">Photo Evidence</h5>
                {selectedSub.images && selectedSub.images.length > 0 ? (
                  <div className="grid grid-cols-3 gap-2">
                    {selectedSub.images.map((img) => (
                      <div key={img.id} className="relative group rounded overflow-hidden border border-[#e2ded5] bg-[#1a1916]">
                        <img
                          src={`http://127.0.0.1:8000/${img.file_path}`}
                          alt="Evidence"
                          className="w-full h-24 object-cover"
                          onError={(e: any) => {
                            e.target.style.display = 'none';
                          }}
                        />
                        <div className="p-1 text-[9px] font-mono text-[#a39e93] truncate bg-[#1a1916]">
                          {img.original_filename || 'Evidence Photo'}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-[#a39e93] font-mono">No photos attached.</div>
                )}
              </div>

              {/* Draft Actions */}
              {selectedSub.status === 'DRAFT' && (
                <div className="flex gap-3 pt-4 border-t border-[#e2ded5]">
                  <button
                    onClick={() => handleSubmitDraft(selectedSub.id)}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#11682f] hover:bg-[#0e5426] text-white text-xs font-mono font-bold uppercase tracking-wider rounded transition-colors"
                  >
                    <Send className="w-4 h-4" /> Submit for Review
                  </button>
                  <button
                    onClick={() => handleDeleteDraft(selectedSub.id)}
                    className="inline-flex items-center gap-1.5 px-3 py-2 bg-[#fde8e7] hover:bg-[#fad2cf] text-[#932720] text-xs font-mono font-bold uppercase tracking-wider rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" /> Delete Draft
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white p-12 rounded border border-[#e2ded5] text-center text-xs font-mono text-[#736f66]">
              Select an observation log to inspect field parameters.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
