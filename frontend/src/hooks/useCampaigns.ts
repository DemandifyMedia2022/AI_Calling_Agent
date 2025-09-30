import { useQuery, useQueryClient } from 'react-query'
import { getCampaigns } from '@/lib/api'

export function useCampaigns() {
  const queryClient = useQueryClient()
  
  const { data, isLoading, error } = useQuery(
    'campaigns',
    getCampaigns,
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
    }
  )

  const refreshCampaigns = () => {
    queryClient.invalidateQueries('campaigns')
  }

  return {
    campaigns: data?.campaigns || [],
    loading: isLoading,
    error,
    refreshCampaigns
  }
}