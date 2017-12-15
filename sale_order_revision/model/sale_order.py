# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013 Agile Business Group sagl (<http://www.agilebg.com>)
#    @author Lorenzo Battistini <lorenzo.battistini@agilebg.com>
#    @author Raphaël Valyi <raphael.valyi@akretion.com> (ported to sale from
#    original purchase_order_revision by Lorenzo Battistini)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp import fields, models, api
from openerp.tools.translate import _
import re


class sale_order(models.Model):
    _inherit = "sale.order"
    current_revision_id = fields.Many2one('sale.order',
                                          'Current revision',
                                          readonly=True,
                                          copy=True)
    old_revision_ids = fields.One2many('sale.order',
                                       'current_revision_id',
                                       'Old revisions',
                                       readonly=True,
                                       context={'active_test': False})
    revision_number = fields.Integer('Revision',
                                     copy=False)
    unrevisioned_name = fields.Char('Order Reference',
                                    copy=True,
                                    readonly=True)
    active = fields.Boolean('Active',
                            default=True,
                            copy=True)

    _sql_constraints = [
        ('revision_unique',
         'unique(unrevisioned_name, revision_number, company_id)',
         'Order Reference and revision must be unique per Company.'),
    ]

    @api.multi
    def copy_quotation(self):
        self.ensure_one()

        # store existing procurement group id, unset it on new revision
        procurement_group_id = self.procurement_group_id.id
        self.write({'procurement_group_id': None})

        revision_self = self.with_context(new_sale_revision=True)
        action = super(sale_order, revision_self).copy_quotation()
        old_revision = self.browse(action['res_id'])
        action['res_id'] = self.id
        self.delete_workflow()
        self.create_workflow()
        self.write({'state': 'draft'})
        msg = _('New revision created: %s') % self.name
        self.message_post(body=msg)
        old_revision.message_post(body=msg)

        # set stored procurement group id on old order
        old_revision.write({'procurement_group_id': procurement_group_id})

        # swap order lines of old and new order
        so_line = self.env['sale.order.line']
        old_lines = so_line.browse(old_revision.order_line.ids)
        new_lines = so_line.browse(self.order_line.ids)
        old_lines.write({'order_id': self.id})
        new_lines.write({'order_id': old_revision.id})

        return action

    @api.returns('self', lambda value: value.id)
    @api.multi
    def copy(self, defaults=None):
        if not defaults:
            defaults = {}
        if self.env.context.get('new_sale_revision'):
            prev_name = self.name
            revno = self.revision_number
            if not re.search('-[0-9][0-9]$', prev_name):
                new_revno = 1
                prev_revno = 0
                new_unrevisioned_name = prev_name
            else:
                prev_revno = revno
                new_revno = revno + 1
                new_unrevisioned_name = self.unrevisioned_name
            new_name = '%s-%02d' % (new_unrevisioned_name, new_revno)

            self.write({'revision_number': new_revno,
                        'unrevisioned_name': new_unrevisioned_name,
                        'name': new_name,
                        })
            defaults.update({'name': prev_name,
                             'revision_number': prev_revno,
                             'unrevisioned_name': new_unrevisioned_name,
                             'active': False,
                             'state': 'cancel',
                             'current_revision_id': self.id,
                             })
        return super(sale_order, self).copy(defaults)

    @api.model
    def create(self, values):
        if 'unrevisioned_name' not in values:
            if values.get('name', '/') == '/':
                seq = self.env['ir.sequence']
                values['name'] = seq.next_by_code('sale.order') or '/'
            values['unrevisioned_name'] = values['name']
        return super(sale_order, self).create(values)
