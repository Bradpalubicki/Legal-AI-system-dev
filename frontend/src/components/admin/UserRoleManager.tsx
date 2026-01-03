'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertTriangle, Shield, Users, UserCheck, UserX, Edit, Save, Plus, Search, Download } from 'lucide-react';

interface UserRole {
  id: string;
  userId: string;
  email: string;
  name: string;
  role: 'admin' | 'attorney' | 'paralegal' | 'staff' | 'client';
  jurisdiction: string[];
  barNumber?: string;
  barAdmissionDate?: string;
  barStatus: 'active' | 'inactive' | 'suspended' | 'not_applicable';
  verificationStatus: 'pending' | 'verified' | 'rejected' | 'expired';
  verificationDate?: string;
  verifiedBy?: string;
  permissions: string[];
  restrictions: string[];
  supervisionRequired: boolean;
  supervisorId?: string;
  lastActive: string;
  createdAt: string;
  updatedAt: string;
  notes: string;
}

interface AttorneyVerification {
  id: string;
  userId: string;
  barNumber: string;
  jurisdiction: string;
  verificationStatus: 'pending' | 'verified' | 'rejected';
  submittedDocuments: string[];
  verificationNotes: string;
  submittedAt: string;
  reviewedAt?: string;
  reviewedBy?: string;
  expirationDate?: string;
}

export default function UserRoleManager() {
  const [users, setUsers] = useState<UserRole[]>([]);
  const [verifications, setVerifications] = useState<AttorneyVerification[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingUser, setEditingUser] = useState<UserRole | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterJurisdiction, setFilterJurisdiction] = useState<string>('all');

  useEffect(() => {
    loadUsers();
    loadVerifications();
  }, []);

  const loadUsers = async () => {
    setLoading(true);

    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/admin/users');
      const data = await response.json();
      setUsers(data.users || []);
    } catch (error) {
      console.error('Failed to load users:', error);
      setUsers([]);
    }

    setLoading(false);
  };

  const loadVerifications = async () => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/admin/verifications');
      const data = await response.json();
      setVerifications(data.verifications || []);
    } catch (error) {
      console.error('Failed to load verifications:', error);
      setVerifications([]);
    }
  };

  const filteredUsers = users.filter(user => {
    if (searchTerm && !user.name.toLowerCase().includes(searchTerm.toLowerCase()) && 
        !user.email.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    if (filterRole !== 'all' && user.role !== filterRole) {
      return false;
    }
    if (filterStatus !== 'all' && user.verificationStatus !== filterStatus) {
      return false;
    }
    if (filterJurisdiction !== 'all' && !user.jurisdiction.includes(filterJurisdiction)) {
      return false;
    }
    return true;
  });

  const saveUser = async () => {
    if (!editingUser) return;

    console.log('Saving user:', editingUser);
    setUsers(prev => prev.map(u => u.id === editingUser.id ? editingUser : u));
    setEditingUser(null);
  };

  const approveVerification = async (userId: string) => {
    setUsers(prev => prev.map(u => 
      u.id === userId 
        ? { 
            ...u, 
            verificationStatus: 'verified',
            verificationDate: new Date().toISOString(),
            verifiedBy: 'current.admin@legal-system.com',
            restrictions: u.restrictions.filter(r => r !== 'verification_pending' && r !== 'no_client_access'),
            permissions: u.role === 'attorney' ? [
              'review_legal_advice',
              'approve_documents', 
              'access_client_data',
              'generate_reports'
            ] : u.permissions
          }
        : u
    ));
  };

  const rejectVerification = async (userId: string) => {
    setUsers(prev => prev.map(u => 
      u.id === userId 
        ? { 
            ...u, 
            verificationStatus: 'rejected',
            verificationDate: new Date().toISOString(),
            verifiedBy: 'current.admin@legal-system.com'
          }
        : u
    ));
  };

  const exportData = () => {
    const exportData = filteredUsers.map(user => ({
      ...user,
      // Redact sensitive information for export
      userId: 'user_***',
      email: user.email.replace(/(.{3}).*(@.*)/, '$1***$2'),
      barNumber: user.barNumber ? user.barNumber.replace(/(.*)-(.{2}).*/, '$1-**$2') : undefined,
      lastActive: '[REDACTED]'
    }));

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `user-roles-report-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      verified: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      expired: 'bg-gray-100 text-gray-800'
    };
    return <Badge className={colors[status as keyof typeof colors]}>{status.toUpperCase()}</Badge>;
  };

  const getRoleBadge = (role: string) => {
    const colors = {
      admin: 'bg-purple-100 text-purple-800',
      attorney: 'bg-blue-100 text-blue-800',
      paralegal: 'bg-green-100 text-green-800',
      staff: 'bg-yellow-100 text-yellow-800',
      client: 'bg-gray-100 text-gray-800'
    };
    return <Badge className={colors[role as keyof typeof colors]}>{role.toUpperCase()}</Badge>;
  };

  const getBarStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-yellow-100 text-yellow-800',
      suspended: 'bg-red-100 text-red-800',
      not_applicable: 'bg-gray-100 text-gray-800'
    };
    return <Badge className={colors[status as keyof typeof colors]}>{status.replace('_', ' ').toUpperCase()}</Badge>;
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading user roles...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Professional Responsibility Notice */}
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-3">
            <Shield className="h-5 w-5 text-amber-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-amber-800">User Role & Attorney Verification Management</h3>
              <p className="text-sm text-amber-700 mt-1">
                This system manages user roles and attorney verification status. All attorney verifications must 
                include valid bar credentials and malpractice insurance. Role changes affecting legal service 
                delivery require supervisor approval.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Users</p>
                <p className="text-2xl font-bold">{users.length}</p>
              </div>
              <Users className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Verified Attorneys</p>
                <p className="text-2xl font-bold text-green-600">
                  {users.filter(u => u.role === 'attorney' && u.verificationStatus === 'verified').length}
                </p>
              </div>
              <UserCheck className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Verifications</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {users.filter(u => u.verificationStatus === 'pending').length}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Supervised Users</p>
                <p className="text-2xl font-bold text-orange-600">
                  {users.filter(u => u.supervisionRequired).length}
                </p>
              </div>
              <UserX className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Verifications Alert */}
      {users.filter(u => u.verificationStatus === 'pending').length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-medium text-yellow-800">Pending Attorney Verifications</h3>
                <p className="text-sm text-yellow-700 mt-1">
                  {users.filter(u => u.verificationStatus === 'pending').length} users require verification review.
                </p>
                <div className="mt-2 space-y-1">
                  {users.filter(u => u.verificationStatus === 'pending').map(user => (
                    <div key={user.id} className="flex items-center justify-between bg-white p-2 rounded">
                      <span className="text-sm text-yellow-700">
                        {user.name} ({user.email}) - {user.role}
                      </span>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          onClick={() => approveVerification(user.id)}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => rejectVerification(user.id)}
                          className="border-red-600 text-red-600 hover:bg-red-50"
                        >
                          Reject
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>User Role Management</span>
            </div>
            <Button onClick={exportData} size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export (Redacted)
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 mb-6">
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="Search by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={filterRole} onValueChange={setFilterRole}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="attorney">Attorney</SelectItem>
                <SelectItem value="paralegal">Paralegal</SelectItem>
                <SelectItem value="staff">Staff</SelectItem>
                <SelectItem value="client">Client</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="verified">Verified</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="expired">Expired</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterJurisdiction} onValueChange={setFilterJurisdiction}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="State" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All States</SelectItem>
                <SelectItem value="CA">CA</SelectItem>
                <SelectItem value="NY">NY</SelectItem>
                <SelectItem value="TX">TX</SelectItem>
                <SelectItem value="FL">FL</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Users Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">User</th>
                  <th className="text-left p-2">Role</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">Bar Status</th>
                  <th className="text-left p-2">Jurisdiction</th>
                  <th className="text-left p-2">Supervision</th>
                  <th className="text-left p-2">Last Active</th>
                  <th className="text-left p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="border-b hover:bg-gray-50">
                    <td className="p-2">
                      <div>
                        <div className="text-sm font-medium">{user.name}</div>
                        <div className="text-xs text-gray-500">{user.email}</div>
                        {user.barNumber && (
                          <div className="text-xs text-gray-500">Bar: {user.barNumber}</div>
                        )}
                      </div>
                    </td>
                    <td className="p-2">
                      {getRoleBadge(user.role)}
                    </td>
                    <td className="p-2">
                      {getStatusBadge(user.verificationStatus)}
                    </td>
                    <td className="p-2">
                      {getBarStatusBadge(user.barStatus)}
                    </td>
                    <td className="p-2">
                      <div className="flex flex-wrap gap-1">
                        {user.jurisdiction.map(j => (
                          <Badge key={j} variant="outline" className="text-xs">{j}</Badge>
                        ))}
                      </div>
                    </td>
                    <td className="p-2">
                      {user.supervisionRequired ? (
                        <Badge className="bg-orange-100 text-orange-800 text-xs">Required</Badge>
                      ) : (
                        <Badge className="bg-gray-100 text-gray-800 text-xs">None</Badge>
                      )}
                    </td>
                    <td className="p-2 text-sm text-gray-500">
                      {new Date(user.lastActive).toLocaleDateString()}
                    </td>
                    <td className="p-2">
                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setEditingUser(user)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        {user.verificationStatus === 'pending' && (
                          <>
                            <Button
                              size="sm"
                              onClick={() => approveVerification(user.id)}
                              className="bg-green-600 hover:bg-green-700 text-xs"
                            >
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => rejectVerification(user.id)}
                              className="border-red-600 text-red-600 hover:bg-red-50 text-xs"
                            >
                              Reject
                            </Button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredUsers.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No users match the current filters.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit User Modal */}
      {editingUser && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Edit User: {editingUser.name}</span>
              <div className="flex space-x-2">
                <Button onClick={saveUser}>
                  <Save className="h-4 w-4 mr-2" />
                  Save
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setEditingUser(null)}
                >
                  Cancel
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Role</label>
                  <Select
                    value={editingUser.role}
                    onValueChange={(value: any) => setEditingUser(prev => 
                      prev ? { ...prev, role: value } : null
                    )}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="admin">Admin</SelectItem>
                      <SelectItem value="attorney">Attorney</SelectItem>
                      <SelectItem value="paralegal">Paralegal</SelectItem>
                      <SelectItem value="staff">Staff</SelectItem>
                      <SelectItem value="client">Client</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Verification Status</label>
                  <Select
                    value={editingUser.verificationStatus}
                    onValueChange={(value: any) => setEditingUser(prev => 
                      prev ? { ...prev, verificationStatus: value } : null
                    )}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="verified">Verified</SelectItem>
                      <SelectItem value="rejected">Rejected</SelectItem>
                      <SelectItem value="expired">Expired</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Bar Number</label>
                  <Input
                    value={editingUser.barNumber || ''}
                    onChange={(e) => setEditingUser(prev => 
                      prev ? { ...prev, barNumber: e.target.value } : null
                    )}
                    placeholder="Enter bar number"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Bar Status</label>
                  <Select
                    value={editingUser.barStatus}
                    onValueChange={(value: any) => setEditingUser(prev => 
                      prev ? { ...prev, barStatus: value } : null
                    )}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                      <SelectItem value="suspended">Suspended</SelectItem>
                      <SelectItem value="not_applicable">Not Applicable</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Jurisdictions (comma-separated)</label>
                  <Input
                    value={editingUser.jurisdiction.join(', ')}
                    onChange={(e) => setEditingUser(prev => 
                      prev ? { 
                        ...prev, 
                        jurisdiction: e.target.value.split(',').map(j => j.trim()).filter(j => j)
                      } : null
                    )}
                    placeholder="CA, NY, TX"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="supervisionRequired"
                    checked={editingUser.supervisionRequired}
                    onChange={(e) => setEditingUser(prev => 
                      prev ? { ...prev, supervisionRequired: e.target.checked } : null
                    )}
                  />
                  <label htmlFor="supervisionRequired" className="text-sm font-medium">
                    Supervision Required
                  </label>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Notes</label>
                  <textarea
                    className="w-full p-2 border rounded-md text-sm"
                    rows={3}
                    value={editingUser.notes}
                    onChange={(e) => setEditingUser(prev => 
                      prev ? { ...prev, notes: e.target.value } : null
                    )}
                  />
                </div>
              </div>

              <div className="md:col-span-2">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Permissions</label>
                    <div className="flex flex-wrap gap-2">
                      {editingUser.permissions.map(permission => (
                        <Badge key={permission} variant="outline" className="text-xs">
                          {permission.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Restrictions</label>
                    <div className="flex flex-wrap gap-2">
                      {editingUser.restrictions.map(restriction => (
                        <Badge key={restriction} variant="outline" className="text-xs bg-red-50 text-red-700">
                          {restriction.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}