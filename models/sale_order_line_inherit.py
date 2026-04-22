import json
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_template_domain = fields.Char(
        compute='_compute_product_template_domain',
        store=False,
    )

    @api.depends('order_id.pricelist_id')
    def _compute_product_template_domain(self):
        for line in self:
            pricelist = line.order_id.pricelist_id
            if pricelist:
                # Buscar los IDs directamente en product.pricelist.item
                template_ids = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', pricelist.id),
                    ('product_tmpl_id', '!=', False),
                ]).mapped('product_tmpl_id').ids

                line.product_template_domain = json.dumps([
                    ('id', 'in', template_ids)
                ])
            else:
                line.product_template_domain = json.dumps([])
    
    @api.onchange('product_template_id','product_uom_qty','product_uom_id','price_unit','tax_ids',)
    def _onchange_order_line(self):
        for line in self:
            apu_related=line.order_id.apu_id
            if apu_related:
                raise ValidationError(f"No puede cambiar las lineas de orden de venta si cuenta con un APU relacionado. \n Por favor dirigete al {apu_related.name} correspondiente si desea aplicar algún ajuste.")