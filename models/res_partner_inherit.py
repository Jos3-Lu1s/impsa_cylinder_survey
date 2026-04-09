from odoo import models, fields, api, _
from datetime import date
from typing import Union

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    code_partner = fields.Char(string="Codigo de contacto", readonly=True, copy=False, index=True)
    
    @api.model
    def create(self, vals_list: Union[dict, list]):
        # Si viene un solo dict, convertirlo en lista
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('code_partner'):
                vals['code_partner'] = self.env['ir.sequence'].next_by_code('res.partner.code') or '0000'

        return super().create(vals_list)