# -*- coding:utf-8 _*-

from django.http import JsonResponse
from step2_Query import Query
import simplejson

q = None


def get_rlt_of_query(request):
    global q

    request.encoding = 'utf-8'
    if request.method != "POST":
        return JsonResponse({"status": 405, "message": "Only POST supported"}, safe=False)
    else:

        req = simplejson.loads(request.body)
        if "jobId" in req:
            jobID = req["jobId"]
        else:
            return JsonResponse({"status": 400, "message": "A job must have a 'jobId' field"}, safe=False)
        if "list" in req:

            content = req['list']
        else:
            return JsonResponse({"status": 400, "message": "A job must have a 'list' field"}, safe=False)

        if content is '':
            return JsonResponse({"status": 400, "message": "Error:list cannot be empty"}, safe=False)
        elif not content:
            return JsonResponse({"status": 400, "message": "Error:list cannot be none"}, safe=False)
        #有不同的任务就切换
        if not q or q.job_id != jobID:
            q = Query(jobID)
        res = q.query(request.body)

        return JsonResponse({"status": 200, "res": res, "JobId": jobID}, safe=False)
