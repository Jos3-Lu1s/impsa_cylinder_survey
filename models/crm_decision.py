from odoo import models, fields

class CrmDecision(models.Model):
    _inherit = "crm.lead"

    test_label = fields.Char(
        string="Texto de prueba",
    )
    
    selection_crm = fields.Selection(
        [('repared', 'Reparación de cilindro'), 
         ('quote', 'Cotización')]
        , string="Tipo de opción")
    