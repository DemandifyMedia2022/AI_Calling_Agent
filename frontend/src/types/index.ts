export interface Lead {
  prospect_name: string
  company_name: string
  job_title: string
  phone: string
  email: string
  timezone: string
}

export interface ApiStatus {
  status: string
  running: boolean
  lead_index: number | null
  campaign: string | null
  campaign_label: string | null
  auto_next: boolean
  lead: Lead | null
}

export interface Campaign {
  key: string
  label: string
}

export interface CsvFile {
  name: string
  size: number
  mtime: number
  active: boolean
}

export interface CsvPreview {
  headers: string[]
  rows: Record<string, string>[]
}

export interface CampaignData {
  name: string
  module: string
  builtin?: boolean
  key?: string
}

export interface ApiResponse<T = any> {
  ok: boolean
  data?: T
  error?: string
}