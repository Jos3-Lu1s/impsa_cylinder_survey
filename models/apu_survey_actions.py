from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError, UserError
from typing import Union

class ApuSurveyActions(models.Model):
    _name="impsa.apu.survey.actions"
    _description = "Listado de acciones en el APU"

    name = fields.Char(
        string="Nombre", required=True, copy=False
    )

    action_code = fields.Char(
        string="Código de acción", copy=False, readonly=True
    )

    @api.model
    def create(self, vals_list: Union[dict, list]):
        # Si viene un solo dict, convertirlo en lista
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('action_code'):
                vals['action_code'] = self.env['ir.sequence'].next_by_code('impsa.apu.survey.actions') or '0000'

        return super().create(vals_list)