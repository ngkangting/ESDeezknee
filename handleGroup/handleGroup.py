from flask import Flask, request, jsonify
from flask_cors import CORS

import os, sys

import requests
from invokes import invoke_http

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
CORS(app)

group_URL = "http://grouping:6103/grouping"
broadcast_URL =  "http://broadcast:6102/broadcast"

@app.route("/handleGroup/create", methods=["POST"])
def create_group():
    if request.is_json:
        try:
            group = request.get_json()
            # print("\nReceived a create group request in JSON:", group)

            result = processCreateGroup(group)
            # return jsonify(result), result["code"]
            return result 


        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "handleGroup.py internal error: " + ex_str
            }), 500

    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400

def processCreateGroup(group):
    createGroup_result = invoke_http(group_URL, method='POST', json=group)

    code = createGroup_result["code"]
    if code not in range(200,300):
        return {
            "code": 500,
            "data": {"createGroup_result": createGroup_result},
            "message": "New group creation failed."
        }

    else: 
        return createGroup_result

    
## incl if statement for when users click on "broadcast group" after group creation
@app.route("/handleGroup/broadcast", methods=["POST"])
def broadcast(): 
    if request.is_json:
        try:
            broadcast_info = request.get_json()
            # print("\nReceived a broadcast request in JSON:", broadcast_info)

            result = processCreateBroadcast(broadcast_info)
            return result

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "handleGroup.py internal error: " + ex_str
            }), 500

    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400

## need to figure out how to link to frontend to get group_id 
def processCreateBroadcast(broadcast_info):
    url = broadcast_URL + "/1"
    createBroadcast_result = invoke_http(url, method='POST', json=broadcast_info)

    code = createBroadcast_result["code"]
    if code not in range(200,300):
        return {
            "code": 500,
            "data": {"createBroadcast_result": createBroadcast_result},
            "message": "Broadcast failed."
        }
    
    else:
        return createBroadcast_result


## if a group chooses to join another group on broadcast listing
## first get all broadcast listing (scenario 1B steps 5, 6)
@app.route("/handleGroup/broadcast_listings")
def getAllBroadcasts():
    all = invoke_http(broadcast_URL, method='GET')

    code = all["code"]
    if code not in range(200,300):
        return {
            "code": 500,
            "data": {"getAllBroadcasts_result": all},
            "message": "Broadcast failed."
        }
    
    else:
        return all

## user from group 2 chooses to join group 1 (scenario 1B step 8)
@app.route("/handleGroup/join_group")
def join_group(): 
    ## get no_of_pax of group 2 from grouping service
    ## figure out how to get grouping_id from frontend
    url_for_noofpax = group_URL + "/2" 
    group_details = invoke_http(url_for_noofpax, method='GET')
    code = group_details["code"]
    if code not in range(200,300):
        return {
            "code": 500,
            "data": {"findNoOfPax_result": group_details},
            "message": "findNoOfPax failed."
        }
    
    else:
        no_of_pax_joining = group_details["data"]["no_of_pax"]

        ## get lf_pax of group 1 from broadcast
        url_for_LFpax = broadcast_URL + "/1"
        broadcast_details = invoke_http(url_for_LFpax, method='GET')
        
        code = broadcast_details["code"]
        if code not in range(200,300):
            return {
                "code": 500,
                "data": {"findLFPax_result": broadcast_details},
                "message": "findNLFPax failed."
            }
        
        else:
            LF_pax = broadcast_details["data"]["lf_pax"]
            
            ## compute new LF_pax
            new_LF_pax = LF_pax - no_of_pax_joining

            # return {"no_of_pax": no_of_pax_joining, "lf_pax": LF_pax, "new_lf_pax": new_LF_pax}

            ## joining group with insufficient space
            if new_LF_pax < 0:
                return jsonify(
                    {
                        "code": 500,
                        "data": {
                            "grouping_id": 2,
                            "message": "Number of pax in your group exceeds limit."
                        }
                    }
                ), 500
            
            ## perfect match
            elif new_LF_pax == 0:
                deletion_details = invoke_http(url_for_LFpax, method='DELETE')
                deletion_of_joining_group = invoke_http(url_for_noofpax, method='DELETE')
                url = group_URL + "/1"
                deletion_of_broadcasting_group = invoke_http(url, method='DELETE')
                code1 = deletion_details["code"]
                code2= deletion_of_joining_group["code"]
                code3 = deletion_of_broadcasting_group["code"]
                if code1 not in range(200,300) or code2 not in range(200,300) or code3 not in range(200,300):
                    return jsonify({
                        "code": 500,
                        "data": {"deleteBroadcast_result": deletion_details},
                        "message": "Failed to join group as deletion of broadcast/group(s) failed."
                    }), 500
                
                else: 
                    new_no_of_pax = LF_pax + no_of_pax_joining
                    merged_group_details = {
                        "description": "Complete group!",
                        "no_of_pax": new_no_of_pax,
                        "status": 1
                    }
                    create_group_result = processCreateGroup(merged_group_details)
                    code = create_group_result["code"]
                    if code not in range(200,300):
                        return jsonify({
                            "code": 500,
                            "data": {"joinGroup_result": create_group_result},
                            "message": "Failed to join group as group creation failed."
                    })

                    else: 
                        ## help how do we get the latest group number????
                        return jsonify(
                            {
                                "code": 200,
                                "message": "Join group success! New group ID is "
                            }
                        ), 200
            
            ## still need more people 
            elif new_LF_pax > 0:
                new_no_of_pax = LF_pax + no_of_pax_joining
                new_grouping_info = {
                    "grouping_id": 1,
                    "no_of_pax": new_no_of_pax,
                    "description": "looking for more members",
                    "status": 0,
                }
                updateGrouping_result = processUpdateGrouping(new_grouping_info)
                code = updateGrouping_result["code"]
                if code not in range(200,300):
                    return jsonify({
                        "code": 500,
                        "data": {"updateGrouping_result": updateGrouping_result},
                        "message": "Failed to join group as group update failed."
                    }), 500
                
                new_broadcast_info = {
                    "grouping_id": 1,
                    "lf_pax": new_LF_pax,
                }
                updateBroadcast_result = processUpdateBroadcast(new_broadcast_info)
                code = updateBroadcast_result["code"]
                if code not in range(200,300):
                        return jsonify({
                            "code": 500,
                            "data": {"updateBroadcast_result": updateBroadcast_result},
                            "message": "Failed to join group as broadcast update failed."
                    }), 500
                else: 
                    return jsonify(
                        {
                            "code": 200,
                            "message": "Join group success! You are now part of group 1. We are in the midst of completing your group."
                        }
                    ), 200
                
                

def processUpdateBroadcast(info):
    url = broadcast_URL + "/1"
    updateBroadcast_result = invoke_http(url, method='PATCH', json=info)

    code = updateBroadcast_result["code"]
    if code not in range(200,300):
        return {
            "code": 500,
            "data": {"updateBroadcast_result": updateBroadcast_result},
            "message": "Failure to join group as broadcast update failed."
        }
    
    else:
        return updateBroadcast_result

def processUpdateGrouping(info):
    url = group_URL + "/1"
    updateGrouping_result = invoke_http(url, method='PATCH', json=info)

    code = updateGrouping_result["code"]
    if code not in range(200,300):
        return {
            "code": 500,
            "data": {"updateGrouping_result": updateGrouping_result},
            "message": "Failure to join group as group update failed."
        }
    
    else:
        return updateGrouping_result

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6104, debug=True)