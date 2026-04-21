from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError, UserError
from typing import Union

class ApuSurveyActions(models.Model):
    _name="impsa.apu.survey.margins"
    _description = "Listado de margenes para el APU"

    name = fields.Char(
        string="Nombre", required=True, copy=False, readonly=True, default="Nuevo"
    )

    percentage=fields.Float(string="Porcentaje",digits=(16, 2),required=True)


    margin_code = fields.Char(
        string="Código de acción", copy=False, readonly=True
    )

    type_cost_margin = fields.Selection([
        ('labour', 'Mano de Obra'),
        ('material', 'Material'),
    ], string="Márgen de Costos ", required=True)

    type_profit_margin = fields.Selection([
        ('indirect_cost', 'Costo Indirecto'),
        ('profit_margin', 'Utilidad'),
    ], string="Tipo", required=True)

    _sql_constraints = [
        (
            'unique_margen_tipo_costo',
            'UNIQUE(percentage, type_cost_margin, type_profit_margin)',
            'Ya existe un margen con el mismo porcentaje, tipo y margen de costos.'
        )
    ]

    @api.constrains('percentage', 'type_cost_margin', 'type_profit_margin')
    def _check_unique_margen(self):
        for rec in self:
            margen_label = dict(rec._fields['type_cost_margin'].selection).get(rec.type_cost_margin)
            tipo_label = dict(rec._fields['type_profit_margin'].selection).get(rec.type_profit_margin)
            duplicado = self.search([
                ('percentage', '=', rec.percentage),
                ('type_cost_margin', '=', rec.type_cost_margin),
                ('type_profit_margin', '=', rec.type_profit_margin),
                ('id', '!=', rec.id),  # excluir el registro actual
            ], limit=1)

            if duplicado:
                raise ValidationError(
                    f'Ya existe un margen con {rec.percentage* 100:.0f}%, '
                    f'tipo "{tipo_label}" y del margen "{margen_label}".'
                )

    @api.model
    def create(self, vals_list: Union[dict, list]):
        # Si viene un solo dict, convertirlo en lista
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('margin_code'):
                vals['margin_code'] = self.env['ir.sequence'].next_by_code('impsa.apu.survey.margins') or '0000'
                vals['name'] = f"{vals['percentage']* 100:.0f} %"

        return super().create(vals_list)
    
    def write(self, vals):
        if 'percentage' in vals:
            vals['name'] = f"{vals['percentage']* 100:.0f} %"
        return super().write(vals)