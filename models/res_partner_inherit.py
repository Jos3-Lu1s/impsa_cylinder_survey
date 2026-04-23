from odoo import models, fields, api, _
from odoo.fields import Domain
from typing import Union

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    display_name = fields.Char(recursive=True)
    code_partner = fields.Char(string="Codigo", help="Codigo de contacto", readonly=True, copy=False, index=True)
    
    @api.model
    def create(self, vals_list: Union[dict, list]):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('code_partner'):
                vals['code_partner'] = self.env['ir.sequence'].next_by_code('res.partner.code') or '0000'

        return super().create(vals_list)
    
    @api.depends('is_company', 'name', 'parent_id.display_name', 'type', 'company_name', 'code_partner')
    def _compute_display_name(self):
        super()._compute_display_name()
        
        for partner in self:
            if partner.code_partner:
                # incluir el código entre corchetes
                partner.display_name = f"[{partner.code_partner}] {partner.display_name}"

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        
        if value:
            domain = Domain(domain) | Domain([('code_partner', operator, value)])
            
        return domain