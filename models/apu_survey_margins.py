from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError, UserError
from typing import Union

class ApuSurveyMargins(models.Model):
    _name="impsa.apu.survey.margins"
    _description = "Listado de margenes para el APU"

    name = fields.Char(
        string="Nombre", 
        compute="_compute_name", 
        store=True, 
        readonly=True
    )

    percentage=fields.Float(string="Porcentaje",digits=(16, 2),required=True)


    margin_code = fields.Char(
        string="Código de margen", copy=False, readonly=True
    )

    type_cost_margin = fields.Selection([
        ('labour', 'Mano de Obra'),
        ('material', 'Material'),
    ], string="Márgen de Costos ", required=True)

    type_profit_margin = fields.Selection([
        ('indirect_cost', 'Costo Indirecto'),
        ('profit_margin', 'Utilidad'),
    ], string="Tipo", required=True)

    _unique_margen_tipo_costo = models.Constraint(
        'UNIQUE(percentage, type_cost_margin, type_profit_margin)',
        'Ya existe un margen con el mismo porcentaje, tipo y margen de costos.'
    )

    @api.depends('percentage')
    def _compute_name(self):
        for rec in self:
            if rec.percentage:
                rec.name = f"{rec.percentage * 100:.0f} %"
            else:
                rec.name = "0 %"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('margin_code'):
                vals['margin_code'] = self.env['ir.sequence'].next_by_code('impsa.apu.survey.margins') or '0000'
        return super().create(vals_list)