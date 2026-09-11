import { createFileRoute, redirect } from '@tanstack/react-router'
import { getJobRedirectUrl } from '#/utils/jobs.functions'

export const Route = createFileRoute('/go/$jobId')({
  loader: async ({ params }) => {
    const url = await getJobRedirectUrl({ data: params.jobId })
    if (url) {
      throw redirect({ href: url })
    }
    throw redirect({ to: '/jobs' })
  },
})
