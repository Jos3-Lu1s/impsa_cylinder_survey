from odoo import models, fields, api
from datetime import date

class SaleOrderSmart(models.Model):
    _inherit = 'sale.order'

    survey_id = fields.Many2one(
        'impsa.cylinder.survey',
        string='Levantamiento'
    )
    
    cylinder_survey_count = fields.Integer(
        string="Levantamientos",
        compute="_compute_cylinder_survey_count"
    )
    
    requeriments_work_order=fields.Text(string="Levantamiento/OT", store=True, readonly=True)
    group_requeriments_work_order=fields.Text(string="Grupo Relacionado", store=True, readonly=True)
    
    delivery_days = fields.Integer(
        string="Días de entrega",
        compute="_compute_delivery_days"
    )

    def _compute_cylinder_survey_count(self):
        for record in self:
            record.cylinder_survey_count = len(record.survey_id)

    def action_view_survey(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Levantamiento',
            'res_model': 'impsa.cylinder.survey',
            'view_mode': 'form',
            'res_id': self.survey_id.id,
        }
        
    def action_print_proforma_custom(self):
        return self.env.ref('impsa_cylinder_survey.action_report_proforma_custom').report_action(self)
    
    @api.depends('commitment_date')
    def _compute_delivery_days(self):
        for record in self:
            if record.commitment_date:
                today = date.today()
                commit_date = record.commitment_date.date() if record.commitment_date else None

                if commit_date:
                    record.delivery_days = (commit_date - today).days
                else:
                    record.delivery_days = 0
            else:
                record.delivery_days = 0