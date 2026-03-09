from odoo import models, fields
class OperationalRecordLine(models.Model):
    _name = 'operational.record.line'
    _description = 'Línea de Registro Operativo'

    _order = 'sequence, id desc'

    parent_id = fields.Many2one(
        'impsa.cylinder.survey',
        string='Levantamiento',
        ondelete='cascade'
    )

    sequence = fields.Integer(string='Secuencia', default=0)
    
    hr = fields.Float(string='Tiempo Estimado')
    work_to_do = fields.Char(
        string='Trabajos a realizar', 
        required=True,
        help="Describe la tarea o trabajo específico a realizar en esta línea."
    )
    obs = fields.Text(string='Dimensiones / Observaciones')