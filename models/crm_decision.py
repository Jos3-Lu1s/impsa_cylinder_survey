from odoo import models, fields

class CrmDecision(models.Model):
    _inherit = "crm.lead"

    
    selection_crm = fields.Boolean(
        string="Reparación de cilindro"
    )
    
    is_won_stage = fields.Boolean(
        related='stage_id.is_won',
        store=True
    )
    
    def action_open_cylinder_survey(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cylinder Survey',
            'res_model': 'impsa.cylinder.survey',  # 👈 tu modelo
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('lead_id', '=', self.id)],  # opcional
            'context': {
                'default_lead_id': self.id
            }
        }