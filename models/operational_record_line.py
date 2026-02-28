from odoo import models, fields
class OperationalRecordLine(models.Model):
    _name = 'operational.record.line'
    _description = 'Operational Record Line'

    parent_id = fields.Many2one(
        'impsa.cylinder.survey',
        string='Parent',
        ondelete='cascade'
    )
    hr = fields.Float(string='Horas')
    work_to_do = fields.Char(string='Trabajos a realizar')
    obs = fields.Text(string='Observaciones')