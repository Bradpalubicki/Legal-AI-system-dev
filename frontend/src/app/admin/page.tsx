export default function AdminPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
        <p className="text-gray-600 mb-8">Feature under development</p>

        <div className="bg-blue-50 border-l-4 border-blue-400 p-6 rounded-lg">
          <div className="flex items-start gap-3">
            <span className="text-2xl">🚧</span>
            <div>
              <h3 className="font-bold text-blue-800 mb-2">Coming Soon</h3>
              <p className="text-blue-700">
                System administration, user management, and compliance monitoring will be available here.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
