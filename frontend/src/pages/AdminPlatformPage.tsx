import React, { useState, useEffect } from 'react';
import {
  Users,
  Shield,
  Activity,
  FileText,
  UserCheck,
  UserX,
  Search,
  CheckCircle2,
  AlertCircle,
  Database,
  BarChart3,
  Calendar,
  Clock,
  Check,
  X,
  Server,
  Cpu,
  RefreshCw,
  Lock
} from 'lucide-react';
import { adminPlatformService } from '../services/api';
import { AdminPlatformStats, AdminUser } from '../types';

export const AdminPlatformPage: React.FC = () => {
  const [stats, setStats] = useState<AdminPlatformStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [auditLog, setAuditLog] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsRes, usersRes, auditRes] = await Promise.allSettled([
        adminPlatformService.getStats(),
        adminPlatformService.getUsers({
          search: searchQuery || undefined,
          role: roleFilter || undefined,
        }),
        adminPlatformService.getAuditLog(30),
      ]);
      if (statsRes.status === 'fulfilled') setStats(statsRes.value);
      if (usersRes.status === 'fulfilled') setUsers(usersRes.value);
      if (auditRes.status === 'fulfilled') setAuditLog(auditRes.value);
    } catch (err) {
      console.error('Failed to load admin platform data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [roleFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      setActionMsg(null);
      await adminPlatformService.updateUserRole(userId, newRole);
      setActionMsg({ type: 'success', text: `User #${userId} role updated to ${newRole}.` });
      await loadData();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to update role.' });
    }
  };

  const handleStatusToggle = async (userId: number, currentActive: boolean) => {
    try {
      setActionMsg(null);
      await adminPlatformService.toggleUserStatus(userId, !currentActive);
      setActionMsg({
        type: 'success',
        text: `User #${userId} account ${!currentActive ? 'activated' : 'suspended'}.`,
      });
      await loadData();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to update status.' });
    }
  };

  const handleApproveRegistration = async (userId: number, action: 'APPROVE' | 'REJECT', targetRole?: string) => {
    try {
      setActionMsg(null);
      await adminPlatformService.approveUser(userId, action, targetRole);
      setActionMsg({
        type: 'success',
        text: `User #${userId} registration ${action === 'APPROVE' ? 'approved' : 'rejected'}.`,
      });
      await loadData();
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to update approval status.' });
    }
  };

  const filteredUsers = users.filter((u) => {
    if (!statusFilter) return true;
    if (statusFilter === 'PENDING') return (u.approval_status || 'APPROVED') === 'PENDING';
    if (statusFilter === 'APPROVED') return (u.approval_status || 'APPROVED') === 'APPROVED';
    if (statusFilter === 'REJECTED') return u.approval_status === 'REJECTED';
    return true;
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#e2ded5] pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold tracking-widest text-[#11682f] uppercase mb-1">
            <Shield className="w-4 h-4 text-[#11682f]" />
            National Platform Administration
          </div>
          <h1 className="text-3xl font-serif font-bold text-[#1f1e1a]">System Admin Control</h1>
          <p className="text-sm text-[#736f66] mt-1">
            Manage user roles, platform permissions, registration approvals, and audit trail security.
          </p>
        </div>
      </div>

      {actionMsg && (
        <div
          className={`flex items-start gap-2.5 p-3.5 rounded border text-xs font-mono ${
            actionMsg.type === 'success'
              ? 'bg-[#d8f3e1] text-[#11682f] border-[#a3e2b8]'
              : 'bg-[#fde2e1] text-[#a8251e] border-[#f9b4b1]'
          }`}
        >
          {actionMsg.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          )}
          <span>{actionMsg.text}</span>
        </div>
      )}

      {/* Top Level Metric Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm">
            <div className="flex items-center justify-between text-xs font-mono text-[#736f66] uppercase tracking-wider mb-2">
              <span>Total Platform Users</span>
              <Users className="w-4 h-4 text-[#11682f]" />
            </div>
            <div className="text-3xl font-serif font-bold text-[#1f1e1a]">{stats.total_users}</div>
            <div className="text-[11px] font-mono text-[#736f66] mt-2 pt-2 border-t border-[#f0ede6]">
              {stats.total_researchers} Researchers · {stats.total_officers} Officers · {stats.total_admins} Admins
            </div>
          </div>

          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm">
            <div className="flex items-center justify-between text-xs font-mono text-[#736f66] uppercase tracking-wider mb-2">
              <span>Observations Verified</span>
              <UserCheck className="w-4 h-4 text-[#11682f]" />
            </div>
            <div className="text-3xl font-serif font-bold text-[#1f1e1a]">{stats.verified_submissions}</div>
            <div className="text-[11px] font-mono text-[#736f66] mt-2 pt-2 border-t border-[#f0ede6]">
              {stats.pending_submissions} pending officer verification
            </div>
          </div>

          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm">
            <div className="flex items-center justify-between text-xs font-mono text-[#736f66] uppercase tracking-wider mb-2">
              <span>Species Inventory</span>
              <Database className="w-4 h-4 text-[#8a5b00]" />
            </div>
            <div className="text-3xl font-serif font-bold text-[#1f1e1a]">{stats.total_species}</div>
            <div className="text-[11px] font-mono text-[#736f66] mt-2 pt-2 border-t border-[#f0ede6]">
              {stats.total_observations.toLocaleString()} Georeferenced Sightings
            </div>
          </div>

          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm">
            <div className="flex items-center justify-between text-xs font-mono text-[#736f66] uppercase tracking-wider mb-2">
              <span>Active in 24h</span>
              <BarChart3 className="w-4 h-4 text-[#11682f]" />
            </div>
            <div className="text-3xl font-serif font-bold text-[#1f1e1a]">{stats.active_users_24h}</div>
            <div className="text-[11px] font-mono text-[#11682f] mt-2 pt-2 border-t border-[#f0ede6]">
              System online & operational
            </div>
          </div>
        </div>
      )}

      {/* Platform Monitoring, Data Ingestion Status & Sensitive Data Protection */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm">
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#11682f] mb-2">
            <Server className="w-4 h-4" />
            <span>Core Infrastructure</span>
          </div>
          <h4 className="font-serif font-bold text-base text-[#1f1e1a] mb-1">FastAPI + PostgreSQL</h4>
          <p className="text-xs text-[#736f66] mb-3 leading-relaxed">
            RESTful API services, JWT session validation, and relational integrity.
          </p>
          <div className="space-y-1.5 pt-2 border-t border-[#f0ede6] text-[11px] font-mono">
            <div className="flex justify-between">
              <span className="text-[#736f66]">Database Engine:</span>
              <span className="font-bold text-[#11682f]">PostgreSQL / SQLite</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#736f66]">Spatial Queries:</span>
              <span className="font-bold text-[#11682f]">PostGIS Active</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#736f66]">Health Check:</span>
              <span className="font-bold text-[#11682f]">200 OK (ONLINE)</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm">
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#0891b2] mb-2">
            <Cpu className="w-4 h-4" />
            <span>ML & RAG Vector Pipeline</span>
          </div>
          <h4 className="font-serif font-bold text-base text-[#1f1e1a] mb-1">Random Forest & Embeddings</h4>
          <p className="text-xs text-[#736f66] mb-3 leading-relaxed">
            384-dimensional vector embeddings, hybrid search, and anomaly detection.
          </p>
          <div className="space-y-1.5 pt-2 border-t border-[#f0ede6] text-[11px] font-mono">
            <div className="flex justify-between">
              <span className="text-[#736f66]">Risk Classifier:</span>
              <span className="font-bold text-[#11682f]">RandomForest (4 tiers)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#736f66]">Anomaly Detector:</span>
              <span className="font-bold text-[#11682f]">IsolationForest Active</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#736f66]">RAG Retrieval:</span>
              <span className="font-bold text-[#0891b2]">Dense + Lexical BM25</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm">
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-[#92400e] mb-2">
            <Lock className="w-4 h-4" />
            <span>Sensitive Data Protection</span>
          </div>
          <h4 className="font-serif font-bold text-base text-[#1f1e1a] mb-1">Species Coordinate Redaction</h4>
          <p className="text-xs text-[#736f66] mb-3 leading-relaxed">
            Exact geolocation coordinates of endangered species are obfuscated from public access.
          </p>
          <div className="space-y-1.5 pt-2 border-t border-[#f0ede6] text-[11px] font-mono">
            <div className="flex justify-between">
              <span className="text-[#736f66]">Public Access:</span>
              <span className="font-bold text-[#b45309]">Obfuscated Coordinates</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#736f66]">Officer Access:</span>
              <span className="font-bold text-[#11682f]">Full Spatial Precision</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#736f66]">Anti-Poaching Filter:</span>
              <span className="font-bold text-[#11682f]">Enforced</span>
            </div>
          </div>
        </div>
      </div>

      {/* User Management Section */}
      <div className="bg-white rounded border border-[#e2ded5] shadow-sm overflow-hidden">
        <div className="p-5 border-b border-[#e2ded5] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 className="font-serif font-bold text-lg text-[#1f1e1a]">User Accounts & Roles</h3>
            <p className="text-xs text-[#736f66]">Approve registrations, assign vetted roles, and manage account status</p>
          </div>

          {/* Search & Filter */}
          <form onSubmit={handleSearch} className="flex flex-wrap gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-3 text-[#736f66]" />
              <input
                type="text"
                placeholder="Search email, username, name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 text-xs font-mono border border-[#d6d2c7] rounded bg-white"
            >
              <option value="">All Statuses</option>
              <option value="PENDING">PENDING APPROVAL</option>
              <option value="APPROVED">APPROVED</option>
              <option value="REJECTED">REJECTED</option>
            </select>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="px-2.5 py-1.5 text-xs font-mono border border-[#d6d2c7] rounded bg-white"
            >
              <option value="">All Roles</option>
              <option value="ADMIN">ADMIN</option>
              <option value="FOREST_OFFICER">FOREST_OFFICER</option>
              <option value="RESEARCHER">RESEARCHER</option>
              <option value="NGO">NGO</option>
              <option value="CITIZEN">CITIZEN</option>
            </select>
          </form>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs font-mono text-[#736f66]">Loading user list...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#e2ded5] bg-[#f9f8f5] text-[#736f66] font-mono uppercase tracking-wider">
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Username</th>
                  <th className="py-3 px-4">Current Role</th>
                  <th className="py-3 px-4">Approval</th>
                  <th className="py-3 px-4">Sightings</th>
                  <th className="py-3 px-4">Verified</th>
                  <th className="py-3 px-4">Last Active</th>
                  <th className="py-3 px-4">Account</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0ede6]">
                {filteredUsers.map((u) => {
                  const isPending = (u.approval_status || 'APPROVED') === 'PENDING';
                  const isRejected = u.approval_status === 'REJECTED';

                  return (
                    <tr key={u.id} className="hover:bg-[#faf9f6]">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-[#1f1e1a]">{u.full_name}</div>
                        <div className="text-[11px] font-mono text-[#736f66]">{u.email}</div>
                      </td>
                      <td className="py-3 px-4 font-mono font-medium text-[#2c2b27]">
                        {u.username || '—'}
                      </td>
                      <td className="py-3 px-4">
                        <select
                          value={u.role_name}
                          onChange={(e) => handleRoleChange(u.id, e.target.value)}
                          className="text-xs font-mono font-bold bg-[#faf9f6] border border-[#d6d2c7] rounded px-2 py-1"
                        >
                          <option value="ADMIN">ADMIN</option>
                          <option value="FOREST_OFFICER">FOREST_OFFICER</option>
                          <option value="RESEARCHER">RESEARCHER</option>
                          <option value="NGO">NGO</option>
                          <option value="CITIZEN">CITIZEN</option>
                        </select>
                      </td>
                      <td className="py-3 px-4">
                        {isPending ? (
                          <div className="flex items-center gap-1.5">
                            <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#fef3c7] text-[#92400e]">
                              PENDING
                            </span>
                            <button
                              onClick={() => handleApproveRegistration(u.id, 'APPROVE')}
                              title="Approve user"
                              className="p-1 rounded bg-[#d8f3e1] text-[#11682f] hover:bg-[#bbf7d0]"
                            >
                              <Check className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => handleApproveRegistration(u.id, 'REJECT')}
                              title="Reject registration"
                              className="p-1 rounded bg-[#fee2e2] text-[#991b1b] hover:bg-[#fecaca]"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ) : isRejected ? (
                          <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#fee2e2] text-[#991b1b]">
                            REJECTED
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#d8f3e1] text-[#11682f]">
                            APPROVED
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-[#2c2b27]">{u.submission_count}</td>
                      <td className="py-3 px-4 font-mono text-[#11682f] font-semibold">{u.verified_count}</td>
                      <td className="py-3 px-4 font-mono text-[#736f66]">
                        {u.last_active_at ? new Date(u.last_active_at).toLocaleDateString() : 'Never'}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                            u.is_active ? 'bg-[#d8f3e1] text-[#11682f]' : 'bg-[#fde2e1] text-[#a8251e]'
                          }`}
                        >
                          {u.is_active ? 'ACTIVE' : 'SUSPENDED'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono">
                        <button
                          onClick={() => handleStatusToggle(u.id, u.is_active)}
                          className={`text-xs font-semibold hover:underline ${
                            u.is_active ? 'text-[#932720]' : 'text-[#11682f]'
                          }`}
                        >
                          {u.is_active ? 'Suspend' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Audit Trail Log */}
      <div className="bg-white rounded border border-[#e2ded5] shadow-sm p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-[#e2ded5] pb-3">
          <div>
            <h4 className="font-serif font-bold text-base text-[#1f1e1a]">System Audit Trail</h4>
            <p className="text-xs text-[#736f66]">Append-only log of security and verification actions</p>
          </div>
          <span className="font-mono text-xs text-[#736f66]">{auditLog.length} recent events</span>
        </div>

        {auditLog.length === 0 ? (
          <div className="text-xs font-mono text-[#736f66] p-4 text-center">No audit records logged yet.</div>
        ) : (
          <div className="space-y-2">
            {auditLog.map((log) => (
              <div
                key={log.id}
                className="flex items-center justify-between p-3 rounded bg-[#faf9f6] border border-[#f0ede6] text-xs font-mono"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      log.action.includes('ROLE')
                        ? 'bg-[#e0e7ff] text-[#3730a3]'
                        : log.action.includes('APPROVAL')
                        ? 'bg-[#fef3c7] text-[#92400e]'
                        : 'bg-[#e2ded5] text-[#2c2b27]'
                    }`}
                  >
                    {log.action}
                  </span>
                  <span className="text-[#1f1e1a]">
                    by <span className="font-bold">{log.actor_name}</span> on {log.entity_type} #{log.entity_id}
                  </span>
                  {log.event_metadata && (
                    <span className="text-[#736f66] text-[11px]">
                      {JSON.stringify(log.event_metadata)}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1 text-[#736f66] text-[11px]">
                  <Clock className="w-3 h-3" />
                  {log.created_at ? new Date(log.created_at).toLocaleString() : '—'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
