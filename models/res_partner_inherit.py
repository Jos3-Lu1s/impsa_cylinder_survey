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
    
    @api.depends('is_company', 'name', 'parent_id.display_name', 'type', 'company_name', 'code_partner')
    def _compute_display_name(self):
        # 1. Ejecutar el comportamiento estándar primero
        super()._compute_display_name()
        
        # 2. Recorrer los registros para inyectar el código
        for partner in self:
            if partner.code_partner:
                # Modificamos el display_name para incluir el código entre corchetes
                partner.display_name = f"[{partner.code_partner}] {partner.display_name}"

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