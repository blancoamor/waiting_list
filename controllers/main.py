# -*- coding: utf-8 -*-
import base64

from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
import openerp.http as http

from openerp.http import request


from openerp.addons.website.models.website import slug

from datetime import datetime
from dateutil.parser import parse
import uuid

import re
import logging
_logger = logging.getLogger(__name__)


class waiting_list_rqst(http.Controller):

    @http.route('/wl/x/<model("waiting.list"):waiting_list>', type='http', auth="public", website=False)
    def waiting_list_index(self, waiting_list):
        error = {}
        default = {}

        return request.render("waiting_list.index", {
            'waiting_list': waiting_list,
        })

    @http.route('/wl/x/<model("waiting.list"):waiting_list>/send', type='json', auth="public", website=False, methods=['POST'])
    def waiting_list_send(self, waiting_list,**post):
        error = {}
        default = {}
        env = request.env(user=SUPERUSER_ID)
        _logger.info("post %r" ,post )
        areas = {'area_id': x  for x in post.get('area_ids')}
        _logger.info("area %r" ,areas )


        t=env['waiting.list.item'].create({'waiting_list_id':waiting_list.id,
                                            'areas_ids':[(4,post.get('area_ids'))],
                                            'phone':post.get('telefono'),
                                            'document':post.get('dni')})
        t.browse()
        return {'name':t['name'],'meeting_point':t['meeting_point']}

