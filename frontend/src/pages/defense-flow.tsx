/**
 * Defense Flow Page
 * Complete legal defense workflow with enforced interview
 */

import { DefenseFlowEnforcer } from '@/components/DefenseFlowEnforcer';

export default function DefenseFlowPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <DefenseFlowEnforcer />
    </div>
  );
}
