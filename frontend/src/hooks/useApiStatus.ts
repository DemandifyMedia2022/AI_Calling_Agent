import { useCallback } from 'react'
import { useQuery, useQueryClient } from 'react-query'
import { getStatus } from '@/lib/api'
import type { ApiStatus } from '@/types'

export function useApiStatus() {
  const queryClient = useQueryClient()
  
  const { data: status, isError } = useQuery<ApiStatus>(
    'status',
    getStatus,
    {
      refetchInterval: 1000, // Poll every second
      refetchIntervalInBackground: true,
      staleTime: 0,
      retry: (failureCount) => {
        // Retry up to 3 times, then stop polling on persistent errors
        return failureCount < 3
      }
    }
  )

  const refreshStatus = useCallback(() => {
    queryClient.invalidateQueries('status')
  }, [queryClient])

  return {
    status: status || {
      status: 'idle',
      running: false,
      lead_index: null,
      campaign: null,
      campaign_label: null,
      auto_next: false,
      lead: null
    },
    isError,
    refreshStatus
  }
}