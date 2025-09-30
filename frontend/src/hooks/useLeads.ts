import { useQuery, useQueryClient } from 'react-query'
import { getLeads } from '@/lib/api'

export function useLeads(page: number) {
  const queryClient = useQueryClient()
  
  const { data, isLoading, error } = useQuery(
    ['leads', page],
    () => getLeads(page),
    {
      staleTime: 2 * 60 * 1000, // 2 minutes
      retry: 2,
      keepPreviousData: true, // Keep previous page data while loading new page
    }
  )

  const refreshLeads = () => {
    queryClient.invalidateQueries(['leads'])
  }

  return {
    leads: data?.leads || [],
    totalPages: data?.total_pages || 1,
    startIndex: data?.start_index || 0,
    totalLeads: data?.total_leads || 0,
    currentPage: data?.page || page,
    loading: isLoading,
    error,
    refreshLeads
  }
}