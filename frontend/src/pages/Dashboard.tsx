import { useQuery } from '@tanstack/react-query'
import { statsApi } from '@/api/stats'
import StatCard from '@/components/StatCard'

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['stats'],
    queryFn: statsApi.getStats,
    refetchInterval: 30000,
  })

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading…</div>
  if (error) return <div className="p-6 text-red-500">Failed to load stats. Log in at /login first.</div>

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">ATEMS Dashboard</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Tools" value={data?.total_tools ?? 0} icon="🔧" />
        <StatCard title="In Stock" value={data?.in_stock ?? 0} icon="✅" />
        <StatCard title="Checked Out" value={data?.checked_out ?? 0} icon="📤" />
        <StatCard title="Calibration Overdue" value={data?.calibration_overdue ?? 0} icon="⚠️" />
      </div>
      <p className="mt-6 text-sm text-muted-foreground">
        React SPA (Phase 7). Use sidebar to navigate to Flask pages.
      </p>
    </div>
  )
}
