from odoo import models, fields

class PurchaseCylinder(models.Model):
    _inherit = "purchase.order"

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Cylinder Survey",
        ondelete="set null"
    )