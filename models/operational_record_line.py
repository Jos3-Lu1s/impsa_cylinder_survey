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
    
    hr = fields.Float(string='Tiempo Estimado')
    work_to_do = fields.Char(
        string='Trabajos a realizar', 
        required=True,
        help="Describe la tarea o trabajo específico a realizar en esta línea."
    )
    obs = fields.Text(string='Dimensiones / Observaciones')

    @api.constrains('hr')
    def _check_positive_hours(self):
        for line in self:
            if line.hr < 0:
                raise ValidationError(_("El tiempo estimado no puede ser negativo en la tarea: %s") % line.work_to_do)