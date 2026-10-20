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
} from 'lucide-react';
import { adminPlatformService } from '../services/api';
import { AdminPlatformStats, AdminUser } from '../types';

export const AdminPlatformPage: React.FC = () => {
  const [stats, setStats] = useState<AdminPlatformStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [auditLog, setAuditLog] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
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
        adminPlatformService.getAuditLog(20),
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
            Manage user roles, platform permissions, observation audit logs, and system integrity.
          </p>
        </div>
      </div>

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

      {/* Platform KPI Metrics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm">
            <div className="flex items-center justify-between text-xs font-mono text-[#736f66] uppercase tracking-wider mb-2">
              <span>Platform Users</span>
              <Users className="w-4 h-4 text-[#11682f]" />
            </div>
            <div className="text-3xl font-serif font-bold text-[#1f1e1a]">{stats.total_users}</div>
            <div className="text-[11px] font-mono text-[#736f66] mt-2 pt-2 border-t border-[#f0ede6]">
              {stats.total_researchers} Researchers · {stats.total_officers} Officers · {stats.total_admins} Admins
            </div>
          </div>

          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm">
            <div className="flex items-center justify-between text-xs font-mono text-[#736f66] uppercase tracking-wider mb-2">
              <span>Submissions Pipeline</span>
              <Activity className="w-4 h-4 text-[#345280]" />
            </div>
            <div className="text-3xl font-serif font-bold text-[#1f1e1a]">{stats.total_submissions}</div>
            <div className="text-[11px] font-mono text-[#736f66] mt-2 pt-2 border-t border-[#f0ede6]">
              {stats.pending_submissions} Pending · {stats.verified_submissions} Verified
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

      {/* User Management Section */}
      <div className="bg-white rounded border border-[#e2ded5] shadow-sm overflow-hidden">
        <div className="p-5 border-b border-[#e2ded5] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 className="font-serif font-bold text-lg text-[#1f1e1a]">User Accounts & Roles</h3>
            <p className="text-xs text-[#736f66]">Assign permissions and manage platform status</p>
          </div>

          {/* Search & Filter */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-3 text-[#736f66]" />
              <input
                type="text"
                placeholder="Search email or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
              />
            </div>
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
                  <th className="py-3 px-4">Current Role</th>
                  <th className="py-3 px-4">Sightings</th>
                  <th className="py-3 px-4">Verified</th>
                  <th className="py-3 px-4">Last Active</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0ede6]">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-[#faf9f6]">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-[#1f1e1a]">{u.full_name || u.email}</div>
                      <div className="text-[11px] font-mono text-[#736f66]">{u.email}</div>
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
                ))}
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
                className="p-2.5 bg-[#faf9f6] rounded border border-[#f0ede6] flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono font-bold px-1.5 py-0.5 bg-[#eae7df] rounded text-[10px] text-[#2c2b27]">
                    {log.action}
                  </span>
                  <span className="text-[#1f1e1a]">
                    Target: <strong className="font-mono">{log.resource_type} #{log.resource_id}</strong>
                  </span>
                </div>
                <div className="font-mono text-[11px] text-[#736f66]">
                  {new Date(log.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
