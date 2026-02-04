interface StatCardProps {
  title: string
  value: string | number
  icon?: string
}

export default function StatCard({ title, value, icon }: StatCardProps) {
  return (
    <div className="bg-card/60 border border-border/50 rounded-lg p-4 hover:bg-card hover:border-primary/40 transition-all">
      <div className="flex justify-between items-start gap-2 mb-2">
        <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  )
}
