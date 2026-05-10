from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class OperationalRecordLine(models.Model):
    _name = 'impsa.operational.record.line'
    _description = 'Línea de Registro Operativo'
    _order = 'sequence, id desc'

    group_id = fields.Many2one(
        'impsa.cylinder.group',
        string='Grupo',
        required=True,
        ondelete='cascade',
        index=True
    )

    survey_id = fields.Many2one(
        'impsa.cylinder.survey',
        string='Levantamiento',
        related='group_id.survey_id',
        store=True,
        index=True
    )

    sequence = fields.Integer(string='Secuencia', default=0)
    
    action_id = fields.Many2one(
        'impsa.apu.survey.actions',
        string='Trabajo a realizar',
        required=True,
        ondelete='restrict',
        help="Seleccione la acción estandarizada a realizar."
    )
    
    obs = fields.Text(string='Dimensiones / Observaciones')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('group_id'):
                group = self.env['impsa.cylinder.group'].browse(vals['group_id'])
                # Si el estado del Survey ya pasó de APU, prohibimos crear
                if group.survey_id.state not in ('draft', 'apu'):
                    raise ValidationError(_("No se pueden agregar operaciones después de que el levantamiento ha salido de la etapa de APU."))
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            if record.survey_id.state not in ('draft', 'apu'):
                raise ValidationError(_("No se pueden modificar operaciones en este estado (%s).") % record.survey_id.state)
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.survey_id.state not in ('draft', 'apu'):
                raise ValidationError(_("No se pueden eliminar operaciones en este estado."))
        return super().unlink()