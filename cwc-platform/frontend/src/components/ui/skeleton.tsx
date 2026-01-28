import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-gray-200", className)}
      {...props}
    />
  )
}

// Pre-built skeleton patterns for common UI elements
function SkeletonCard() {
  return (
    <div className="rounded-lg border bg-white p-4 space-y-3">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-4 w-full" />
    </div>
  )
}

function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}

function SkeletonList({ items = 3 }: { items?: number }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: items }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}

function SkeletonStats({ count = 4 }: { count?: number }) {
  return (
    <div className={`grid gap-4 md:grid-cols-${count}`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-lg border bg-white p-4 space-y-2">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-8 w-24" />
        </div>
      ))}
    </div>
  )
}

export { Skeleton, SkeletonCard, SkeletonTable, SkeletonList, SkeletonStats }
