from odoo import models, fields
class OperationalRecordLine(models.Model):
    _name = 'operational.record.line'
    _description = 'Línea de Registro Operativo'

    parent_id = fields.Many2one(
        'impsa.cylinder.survey',
        string='Levantamiento',
        ondelete='cascade'
    )
    hr = fields.Float(string='Tiempo Estimado')
    work_to_do = fields.Char(string='Trabajos a realizar')
    obs = fields.Text(string='Dimensiones / Observaciones')