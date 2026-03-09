export default function DashboardLoading() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
        <p className="text-sm text-gray-500">Loading...</p>
      </div>
    </div>
  );
}
