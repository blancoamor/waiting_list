# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime , timedelta ,  date
from dateutil import parser

from openerp import models, fields, api ,  SUPERUSER_ID
from openerp import tools


from openerp.tools.translate import _
import re
import logging

import requests
from lxml import etree

_logger = logging.getLogger(__name__)




class waiting_list(models.Model):

    _name = 'waiting.list'
    _description = 'waiting list'

    name = fields.Char(string="name")
    section_id = fields.Many2one('crm.case.section',string="Section")
    areas_ids = fields.Many2many('waiting.list.area','waiting_list_id',string="areas")
  
    last_use_date_a = fields.Date('Fecha', default=date.today())
    last_number_a = fields.Integer(string='Ultimo numero', default=0)
    last_use_date_b = fields.Date('Fecha', default=date.today())
    last_number_b = fields.Integer(string='Ultimo numero', default=0)
    active_user_ids = fields.One2many('waiting.list.active_users','waiting_list_id',string="active users")


class waiting_list_saleman_in_out(models.TransientModel):
    _name = "waiting.list.saleman_in_out"
    _description = 'Set attention'


    name = fields.Char(compute="_compute_action_name")
    waiting_list_id = fields.Many2one('waiting.list')
    user_id = fields.Many2one('res.users')

    @api.depends('waiting_list_id','user_id')
    def _compute_action_name(self):
        self.name = "%s %s" % (self.waiting_list_id.name , self.user_id.name)

    @api.multi
    def saleman_in(self):


        view = { 
            'name':"Lista",
            'view_mode': 'tree',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'waiting.list.item',
            'type': 'ir.actions.act_window',
            'nodestroy': True,

            'target': 'self',
            'context': [{'waiting_list_id':self[0].waiting_list_id.id}],
            'domain': [('waiting_list_id','=',self[0].waiting_list_id.id)],
        }


        for user in self[0].waiting_list_id.active_user_ids:
            if self._uid == user.user_id.id :
                return view

        self.env['waiting.list.active_users'].create({'user_id':self[0].user_id.id,'waiting_list_id':self[0].waiting_list_id.id})

        return view

    @api.one
    def saleman_out(self):
        self.env['waiting.list.active_users'].search([('user_id','=',self.user_id.id),
                                                      ('waiting_list_id','=',self.waiting_list_id.id)]).unlink()


class waiting_list_saleman_in_out_log(models.Model):

    _name = 'waiting.list.saleman_in_out.log'
    _description = 'waiting_list_saleman_in_out_log'

    list_item_id = fields.Many2one('waiting.list.item')
    datetime = fields.Datetime('Fecha', default=datetime.now())
    user_id = fields.Many2one('res.users')



class waiting_list_area(models.Model):

    _name = 'waiting.list.area'
    _description = 'waiting list'

    waiting_list_id = fields.Many2one('waiting.list')
    name = fields.Char()
    meeting_point = fields.Char()
    image = fields.Binary()

class waiting_list_active_users(models.Model):

    _name = 'waiting.list.active_users'
    _description = 'waiting list'
    _rec_name = 'user_id'
    waiting_list_id = fields.Many2one('waiting.list')
    user_id = fields.Many2one('res.users')


class waiting_list_item(models.Model):

    _name = 'waiting.list.item'
    _description = 'waiting list item'
  


    @api.model
    def create(self,vals):
        waiting_list_id = self.env['waiting.list'].browse([vals['waiting_list_id']])
        if 'document' in vals :
            partner_id =self.env['res.partner'].search([('document_number','=',vals['document'])],limit=1)
            list_name='a'
            if partner_id :
                vals['partner_id']=partner_id.id                
                list_active_users = [x.user_id.id for x in waiting_list_id.active_user_ids ]
                orders=self.env['sale.order'].search([
                                                          ('partner_id','=',partner_id.id),
                                                          #('section_id','=',self.waiting_list_id.section_id.id),
                                                          ('state','not in',['done','cancel','draft'])
                                                          ])
                if orders :
                    list_name='b'

                order_uids = [x.user_id.id for x in orders ]
                user_intersec = set(order_uids).intersection(list_active_users)
                if user_intersec :
                    vals['proposed_user_id'] = user_intersec.pop()
                

        # date.today() == waiting_list_id.last_use_date_a and
        if  waiting_list_id['last_number_' + list_name] < 100 :
            next=waiting_list_id['last_number_' + list_name] + 1
            waiting_list_id.write({'last_number_'+ list_name:next})
        else :
            next= 1
            waiting_list_id.write({'last_number_'+ list_name:next,'last_use_date_'+ list_name:date.today()})
       
        vals['name']=list_name.upper() + str(next)
        #vals['meeting_point']=waiting_list_id['meeting_point']
        vals['state'] = 'wait'
        vals['log_ids']=[(0,0,{'name':'wait','user_id':self._uid})]
        rec = super(waiting_list_item, self).create(vals)   
        return rec


    @api.one
    def write(self,vals):
        if 'state' in vals :
           vals['log_ids']=[(0,0,{'name':vals['state'],'user_id':self._uid})]
        rec = super(waiting_list_item, self).write(vals)   
        return rec


    @api.one
    def require(self):
        vals={}
        vals['user_id']=self._uid
        vals['state']='call'
        self.write(vals)


    @api.one
    def attention(self):
        vals={}
        vals['user_id']=self._uid
        vals['state']='attention'
        self.write(vals)

    @api.one
    def cancelar(self):
        vals={}
        vals['user_id']=self._uid
        vals['state']='cancel'
        self.write(vals)

    name = fields.Char()
    datetime = fields.Date('Fecha', default=datetime.now())

    state = fields.Selection([('draft','Borrador'),('wait','Espera'),('call','Llamado'),('attention','En atencion'),('cancel','Cancelado'),('done','Realizado')],default='draft')

    waiting_list_id = fields.Many2one('waiting.list',required=True)
    #section_id = fields.Many2one('crm.case.section',related='waiting_list_id.section_id')

    user_id = fields.Many2one('res.users')
    proposed_user_id = fields.Many2one('res.users')

    partner_id = fields.Many2one('res.partner')
    areas_ids = fields.Many2many('waiting.list.area','waiting_list_item_area_rel','item_id','area_id','Areas' ,required=True)
    meeting_point = fields.Char()

    phone = fields.Char()
    document = fields.Char()
    log_ids = fields.One2many('waiting.list.item.log','list_item_id')
    orders_ids = fields.Many2many(comodel_name='sale.order',
                            relation='list_item_sale_order_rel',
                            column1='list_id',
                            column2='order_id')


class waiting_list_item_log(models.Model):

    _name = 'waiting.list.item.log'
    _description = 'waiting list'

    list_item_id = fields.Many2one('waiting.list.item')
    name = fields.Selection([('draft','Borrador'),('wait','Espera'),('call','Llamado'),('attention','En atencion'),('cancel','Cancelado'),('done','Realizado')],default='draft')
    datetime = fields.Datetime('Fecha', default=datetime.now())
    user_id = fields.Many2one('res.users')
