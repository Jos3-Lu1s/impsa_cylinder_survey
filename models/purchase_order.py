from odoo import models, fields

class PurchaseCylinder(models.Model):
    _inherit = "purchase.order"

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Levantamiento de Cilindro",
        ondelete="set null",
        index=True,
        copy=False
    )