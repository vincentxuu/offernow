import { createFileRoute, redirect } from '@tanstack/react-router'
import { getJobRedirectUrlById } from '#/utils/d1.server'
import { getJobRedirectUrl } from '#/utils/jobs.functions'

export const Route = createFileRoute('/go/$jobId')({
  server: {
    handlers: {
      GET: async ({ params, request }) => {
        const url = await getJobRedirectUrlById(params.jobId)
        if (url) {
          return Response.redirect(url, 302)
        }
        return Response.redirect(new URL('/jobs', request.url), 302)
      },
    },
  },
  loader: async ({ params }) => {
    const url = await getJobRedirectUrl({ data: params.jobId })
    if (url) {
      throw redirect({ href: url })
    }
    throw redirect({ to: '/jobs' })
  },
})
