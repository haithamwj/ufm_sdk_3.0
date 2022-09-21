#
# Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
from google.protobuf.any_pb2 import Any
import google.protobuf.timestamp_pb2
import requests
import time
from datetime import datetime
from threading import Lock
import plugins.grpc_streamer_plugin.ufm_sim_web_service.grpc_plugin_streamer_pb2 as grpc_plugin_streamer_pb2
from plugins.grpc_streamer_plugin.ufm_sim_web_service.Config import RESTCall,Constants

class Destination:
    job_id_messages = 1
    lock = Lock()

    def __init__(self, ip, rests_calls, session, host):
        self.dest_ip = ip
        self.calls = []
        self.threads = []
        self.stop_all = False
        self._session = session
        self._host = host
        self.processing_calls(rests_calls)
        self.queue = None
        self.callback = None

    def processing_calls(self, rests_calls):
        if rests_calls is None:return
        for call in rests_calls:
            is_tuple = isinstance(call,tuple)
            name = call[0] if is_tuple else call
            name = name.capitalize()
            if RESTCall.__contains__(name):
                interval = call[1] if len(call) > 1 and is_tuple else Constants.REST_DEFAULT_INTERVAL
                delta = call[2] if len(call) > 2 and is_tuple else Constants.REST_DEFAULT_DELTA
                location = RESTCall[name].location
                tuple_data = (name, interval, delta, location)
                self.calls.append(tuple_data)
            else:
                print(f'{name} could not be added, it is not in rest apis')

    def thread_task(self, call, queue, callback):
        name, interval, delta, location = call[0], call[1], call[2], RESTCall[call[0]].location
        last_id = None
        self.queue = queue
        self.callback = callback
        while not self.stop_all:
            result = self.send_get_request(location)
            if result.status_code != 200:
                break
            if delta:
                result, last_id = self.extract_new_data(result.json(), last_id)
            else:
                result = result.json()

            for item in result:
                params = str(item)
                message = self._encode_results_(name, params)
                queue.put(message) # sending the result to main thread
            if len(result) > 0 and callback:
                callback.put(self.new_data_callback) # calling a callback to get this result
            time.sleep(interval) # sleep for some time


    def new_data_callback(self):
        return self.dest_ip

    def extract_new_data(self, results, last_id):
        #tolikin builds delta function
        output = []
        if len(results) == 0 or "id" not in results[0]:
            return results, 0

        next_last_id = 0 if last_id is None else last_id #get the last id or 0

        #bring only the apis after that id
        for item in results:
            if int(item["id"]) > next_last_id:
                output.append(item)
                next_last_id = max(item["id"], next_last_id)
        return output, next_last_id

    def all_result(self):
        messages = []
        for call in self.calls:
            respond = self.send_get_request(call[3])
            if respond.status_code != 200:
                continue
            data = respond.json()
            if not isinstance(data, list):
                continue
            for element in data:
                messages.append((call[0], str(element)))

        output = []
        for message in messages:
            output.append(self._encode_results_(message[0], message[1]))

        return output

    def serialization(self):
        if not(self.callback and self.queue):
            return
        for call in self.calls:
            respond = self.send_get_request(call[3])
            if respond.status_code != 200:
                continue
            data = respond.json()

            for item in data:
                params = str(item)
                message = self._encode_results_(call[0], params)
                self.queue.put(message)  # sending the result to main thread
            if len(data) > 0 and self.callback:
                self.callback.put(self.new_data_callback)

    def to_message(self):
        params = []
        for item in self.calls:
            params.append(grpc_plugin_streamer_pb2.DestinationParams.APIParams(name=item[0],
                                                                               interval=item[1], only_delta=item[2]))
        if len(self.calls)==0:
            raise Exception(Constants.LOG_NO_REST_DESTINATION)
        return grpc_plugin_streamer_pb2.DestinationParams(ip=self.dest_ip, apiParams=params)

    def _encode_results_(self, task_name, params):
        des_message = grpc_plugin_streamer_pb2.gRPCStreamerParams()
        des_message.task_name = task_name
        des_message.data = str(params)
        timestamp = google.protobuf.timestamp_pb2.Timestamp()
        timestamp.FromDatetime(datetime.now())
        des_message.timestamp.CopyFrom(timestamp)
        des_message.job_id = str(Destination.job_id_messages)
        with Destination.lock:
            Destination.job_id_messages += 1
        return des_message

    def send_get_request(self, resource_path):
        if self._host is None or self._session is None:return None
        if ':' in self._host:
            url = 'https://[{0}]{1}'.format(self._host, resource_path)
        else:
            url = 'https://{0}{1}'.format(self._host, resource_path)
        try:
            respond = self._session.get(url)
            return respond
        except requests.ConnectionError as e:
            print("Wasn't able to reach " + resource_path + ". Connection Error, please see this exception.\n" + str(e))
        except requests.Timeout as e:
            print("Wasn't able to reach " + resource_path + ". Timeout Error, please see this exception.\n" + str(e))
        except requests.RequestException as e:
            print("Wasn't able to reach " + resource_path + ". Request Error, please see this exception.\n" + str(e))
        except KeyboardInterrupt as e:
            print("Wasn't able to reach " + resource_path + ". Connection Error, please see this exception.\n" + str(e))
        return None
