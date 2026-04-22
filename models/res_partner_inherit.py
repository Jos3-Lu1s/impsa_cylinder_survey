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
    
    """ @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        domain = domain or []
        if name:
            domain = [
                '|', '|',
                ('name', operator, name),
                ('ref', operator, name),
                ('code_partner', operator, name),  # ← campo personalizado
            ] + domain
            return self._search(domain, limit=limit, order=order)
        return super()._name_search(name, domain, operator, limit, order) """
    @api.model
    def _search_display_name(self, operator, value):
        if value:
            return [
                '|',
                ('name', operator, value),
                ('code_partner', operator, value),
            ]
        return super()._search_display_name(operator, value)