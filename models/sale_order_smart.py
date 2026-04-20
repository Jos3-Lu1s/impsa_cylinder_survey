from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError
class SaleOrderSmart(models.Model):
    _inherit = 'sale.order'

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Levantamiento de Origen",
        ondelete="set null",
        copy=False,
        help="Levantamiento técnico del cual se generó esta cotización."
    )
    
    cylinder_survey_count = fields.Integer(
        string="Levantamientos",
        compute="_compute_cylinder_survey_count"
    )
    
    requeriments_work_order=fields.Text(string="Levantamiento/OT", store=True, readonly=True)
    group_requeriments_work_order=fields.Text(string="Grupo Relacionado", store=True, readonly=True)
    
    delivery_days = fields.Integer(
        string="Días de entrega",
        compute="_compute_delivery_days"
    )
    apu_id = fields.Many2one(
        'impsa.apu.survey',
        string="APU Relacionado",
        ondelete="set null",
        copy=False
    )
    
    apu_survey_count = fields.Integer(
        string="APU",
        compute="_compute_apu_survey_count"
    )

    """ product_domain = fields.Json(compute='_compute_product_domain', store=False) """

    @api.depends('partner_id')
    def _compute_product_domain(self):
        for record in self:
            if record.partner_id:
                # Buscar lista de precios que tenga asignado este contacto
                pricelist = self.env['product.pricelist'].search([
                    ('contacto_id', '=', record.partner_id.id)  # ← nombre de tu campo Many2one
                ], limit=1)
                if pricelist:
                    items = self.env['product.pricelist.item'].search([
                        ('pricelist_id', '=', pricelist.id),
                        ('applied_on', 'in', ['0_product_variant', '1_product'])
                    ])

                    product_ids = []
                    for item in items:
                        if item.applied_on == '0_product_variant':
                            product_ids.append(item.product_id.id)
                        elif item.applied_on == '1_product':
                            product_ids += item.product_tmpl_id.product_variant_ids.ids

                    if product_ids:
                        record.product_domain = json.dumps([('id', 'in', list(set(product_ids)))])
                    else:
                        record.product_domain = json.dumps([])
                else:
                    record.product_domain = json.dumps([])
            else:
                record.product_domain = json.dumps([])

    @api.depends('survey_id')
    def _compute_cylinder_survey_count(self):
        for record in self:
            record.cylinder_survey_count = 1 if record.survey_id else 0

    @api.depends('apu_id')
    def _compute_apu_survey_count(self):
        for record in self:
            record.apu_survey_count = 1 if record.apu_id else 0

    def action_view_survey(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Levantamiento',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'form',
            'res_id': self.survey_id.id,
        }
        
    def action_print_proforma_custom(self):
        return self.env.ref('impsa_cylinder_survey.action_report_proforma_custom').report_action(self)
    
    @api.depends('commitment_date')
    def _compute_delivery_days(self):
        for record in self:
            if record.commitment_date:
                today = date.today()
                commit_date = record.commitment_date.date() if record.commitment_date else None

                if commit_date:
                    record.delivery_days = (commit_date - today).days
                else:
                    record.delivery_days = 0
            else:
                record.delivery_days = 0

    def action_view_apu_survey(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'APU',
            'res_model': 'impsa.apu.survey',
            'view_mode': 'form',
            'res_id': self.apu_id.id,
        }

    @api.onchange('partner_id')
    def _onchange_select_pricelist(self):
            pricelist = self.env['product.pricelist'].search([
                        ('contacto_id', '=', self.partner_id.id)  # ← nombre de tu campo Many2one
                    ], limit=1)
            if self.partner_id:
                self.pricelist_id=pricelist.id
                #raise ValidationError(f"La lista de precios es {pricelist}")

    """ @api.depends('partner_id', 'pricelist_id')
    def _compute_product_domain(self):
        for record in self:
            if record.pricelist_id:
                items = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', record.pricelist_id.id),
                ])

                template_ids = items.mapped('product_tmpl_id').ids

                _logger.info(">>> Templates encontrados: %s", template_ids)
                record.product_domain = [('id', 'in', template_ids)] if template_ids else []
            else:
                record.product_domain = [] """
  