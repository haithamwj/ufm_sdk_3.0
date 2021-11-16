"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2021. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nahum Kilim
@date:   September 20, 2021
"""

import configparser
import json

from flask import Flask
from flask_restful import Api
import logging
from logging.handlers import RotatingFileHandler
import os
from apscheduler.schedulers.background import BackgroundScheduler

from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from twisted.web import server

from resources import UFMResource, Compare, Ndts, Reports, ReportId,\
    UploadMetadata, Delete, Cancel, Version, Help, Dummy


class UFMWebSim:
    def parse_config(self):
        ndt_config = configparser.ConfigParser()
        if os.path.exists(UFMResource.config_file_name):
            ndt_config.read(UFMResource.config_file_name)
            self.log_level = ndt_config.get("Common", "log_level")
            self.log_file_max_size = ndt_config.getint("Common", "log_file_max_size")
            self.log_file_backup_count = ndt_config.getint("Common", "log_file_backup_count")
            mode = ndt_config.get("Common", "mode")

            log_format = '%(asctime)-15s %(levelname)s %(message)s'
            logging.basicConfig(handlers=[RotatingFileHandler(self.log_file_path,
                                                              maxBytes=self.log_file_max_size,
                                                              backupCount=self.log_file_backup_count)],
                                level=logging.getLevelName(self.log_level),
                                format=log_format)

    def init_apis(self):
        default_apis = {
            Ndts: "/list",
            Reports: "/reports",
            Delete: "/delete",
            UploadMetadata: "/upload_metadata",
            ReportId: "/reports/<report_id>",
            Version: "/version",
            Help: "/help",
            Dummy: "/dummy",
        }
        for resource, path in default_apis.items():
            self.api.add_resource(resource, path)

        self.api.add_resource(Cancel, "/cancel", resource_class_kwargs={'scheduler': self.scheduler})
        self.api.add_resource(Compare, "/compare", resource_class_kwargs={'scheduler': self.scheduler})

    def restart_periodic_comparison(self):
        if not os.path.exists(UFMResource.periodic_request_file):
            return
        compare = Compare(self.scheduler)
        with open(UFMResource.periodic_request_file, "r") as file:
            compare.parse_request(json.load(file))
        compare.start_scheduler()

    def __init__(self):
        self.log_level = logging.INFO
        self.log_file_max_size = 10240000
        # self.log_file_path = "/tmp/ndt.log"
        self.log_file_path = "/log/ndt.log"
        self.log_file_backup_count = 5
        self.port_number = 8980
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.parse_config()
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.restart_periodic_comparison()
        self.init_apis()

    async def run(self):
        self.app.run(port=self.port_number, debug=True)
        # resource = WSGIResource(reactor, reactor.getThreadPool(), self.app)
        # reactor.listenTCP(self.port_number, server.Site(resource))
        # reactor.run()

    async def stop(self):
        pass
