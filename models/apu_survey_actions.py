from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError, UserError
from typing import Union

class ApuSurveyActions(models.Model):
    _name="impsa.apu.survey.actions"
    _description = "Listado de acciones en el APU"

    name = fields.Char(
        string="Nombre", 
        required=True, 
        copy=False
    )

    action_code = fields.Char(
        string="Código de acción", 
        copy=False, 
        readonly=True,
        default=lambda self: _('Nuevo')
    )

    _action_code_uniq = models.Constraint(
        'UNIQUE(action_code)',
        'El código de acción debe ser único, ya existe un registro con este código.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('action_code') or vals.get('action_code') == _('Nuevo'):
                vals['action_code'] = self.env['ir.sequence'].next_by_code('impsa.apu.survey.actions') or '00000'
                
        return super().create(vals_list)