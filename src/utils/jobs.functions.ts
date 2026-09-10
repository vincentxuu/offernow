import { createServerFn } from '@tanstack/react-start'
import type { Job } from './types'

async function loadJobsFromJSON(): Promise<Job[]> {
  try {
    const { default: data } = await import('../../scripts/data/jobs.json')
    return data as Job[]
  } catch {
    return []
  }
}

export const getJobs = createServerFn().handler(async (): Promise<Job[]> => {
  return loadJobsFromJSON()
})
