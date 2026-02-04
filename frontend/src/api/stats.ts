import apiClient from './client'

export interface Stats {
  total_tools: number
  checked_out: number
  in_stock: number
  calibrated_tools: number
  calibration_overdue: number
}

export const statsApi = {
  getStats: async (): Promise<Stats> => {
    const { data } = await apiClient.get<Stats>('/api/stats')
    return data
  },
}
