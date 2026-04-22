from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError, UserError
from typing import Union

class MarginPasswordWizard(models.TransientModel):
    _name = 'impsa.apu.survey.passw'
    _description = 'Verificación de contraseña'

    password = fields.Char(string='Contraseña', password=True)

    def action_confirm(self):
        # Obtener contraseña desde parámetros del sistema
        stored = self.env['ir.config_parameter'].sudo().get_param(
            'view.impsa.passw'
        )
        if self.password != stored:
            raise UserError('Contraseña incorrecta.')

        # Redirigir a la vista real
        return {
            'type': 'ir.actions.act_window',
            'name': 'Catálogo de Márgenes',
            'res_model': 'impsa.apu.survey.margins',
            'view_mode': 'list'
        }