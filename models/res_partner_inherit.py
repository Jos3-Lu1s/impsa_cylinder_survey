from odoo import models, fields, api, _
from odoo.osv import expression
from datetime import date
from typing import Union

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    code_partner = fields.Char(string="Codigo de contacto", readonly=True, copy=False, index=True)
    
    @api.model
    def create(self, vals_list: Union[dict, list]):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('code_partner'):
                vals['code_partner'] = self.env['ir.sequence'].next_by_code('res.partner.code') or '0000'

        return super().create(vals_list)
    
    @api.model
    def _search_display_name(self, operator, value): # type: ignore
        # obtenemos primero el dominio nativo
        domain = super()._search_display_name(operator, value)
        
        if value:
            # combinamos el dominio original con nuestra nueva regla
            domain = expression.OR([
                domain,
                [('code_partner', operator, value)]
            ])
            
        return domain 