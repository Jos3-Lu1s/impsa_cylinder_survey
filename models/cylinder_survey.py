from odoo import models, fields, api
from . import operational_record_line


class CylinderSurvey(models.Model):
    _name = "impsa.cylinder.survey"
    _description = "Levantamiento de Cilindros (F-05-01)"

    # Heredar de mail.thread y mail.activity.mixin
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Referencia", required=True, copy=False, readonly=True, default="Nuevo"
    )

    partner_id = fields.Many2one(
        "res.partner", string="Cliente", required=True, tracking=True
    )
    diameter_sleeve = fields.Char(string="Ø Camisa")
    date = fields.Date(string="Fecha", default=fields.Date.context_today)
    description = fields.Char(string="Descripción", default="Cilindro Hidráulico")
    diameter_rod = fields.Char(string="Ø Vástago")
    work_order = fields.Char(string="Orden de Trabajo")
    cylinder_type = fields.Char(string="Cilindro de")
    stroke = fields.Float(string="Carrera")
    serial_number = fields.Char(string="No. Serie")
    part_number = fields.Char(string="No. Parte")

    internal_notes = fields.Html(
        string="Notas Internas",
        help="Espacio para notas detalladas sobre este registro.",
    )

    operational_record_ids = fields.One2many(
        "operational.record.line", 
        "parent_id",
        string="Registro Operativo",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("impsa.cylinder.survey")
                    or "Nuevo"
                )

        return super(CylinderSurvey, self).create(vals_list)
