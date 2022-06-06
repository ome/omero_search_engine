from . import searchresults
from flask import request, jsonify

from omero_search_engine.api.v1.resources.utils import search_resource_annotation
@searchresults.route('/',methods=['GET'])
def search_resource():
    task_id=request.args.get("task_id")
    if not task_id:
        return "Errro, No search id is provided."
    task = search_resource_annotation.AsyncResult(task_id)
    if not task:
        return jsonify(
            {"Status": "not found", "Error": "There is not task has {id} id".format(id=task_id), "Results  ": {}})


    if task.status=="FAILURE":
        return jsonify({"Status": task.status, "Results": str(task.info)})

    return jsonify({"Status": task.status, "Results": task.info})

@searchresults.route('/status/<task_id>')
def taskstatus(task_id):
    '''
    check a task status  using its id
    '''
    task = search_resource_annotation.AsyncResult(task_id)
    if task:
        return jsonify({"Status":task.status, "Results  ": task.info})
    else:
        return jsonify({"Status":"not found","Error":"There is not task has {id} id".format(id=task_id), "Results  ": {}})
