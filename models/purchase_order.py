from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PurchaseCylinder(models.Model):
    _inherit = "purchase.order"

    survey_id = fields.Many2one(
        "impsa.cylinder.survey",
        string="Levantamiento de Cilindro",
        ondelete="set null",
        index=True,
        copy=False
    )
    
    cylinder_survey_count = fields.Integer(
        string="Levantamientos",
        compute="_compute_cylinder_survey_count"
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
        
    def button_confirm(self):
        for order in self:
            products_without_code = order.order_line.filtered(
                lambda l: not l.product_id.default_code
            )

            if products_without_code:
                product_names = ", ".join(
                    products_without_code.mapped('product_id.display_name')
                )

                raise ValidationError(_(
                    "No puedes confirmar la Orden de Compra porque los siguientes productos no tienen código interno (default_code):\n%s"
                ) % product_names)

        return super().button_confirm()
        
    