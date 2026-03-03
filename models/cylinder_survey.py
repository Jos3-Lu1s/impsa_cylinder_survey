from odoo import models, fields, api
from odoo.exceptions import ValidationError

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
    description = fields.Char(string="Descripción")
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

    total_tasks = fields.Integer(
        string='Total de Tareas',
        compute='_compute_operational_totals',
        store=True,
        help="Suma total de líneas en el registro operativo.",
        readonly=True
    )
    total_hours = fields.Float(
        string='Total de Horas',
        compute='_compute_operational_totals',
        store=True,
        help="Suma total de horas de todas las tareas.",
        readonly=True
    )
    state = fields.Selection([
        ('draft', 'Levantamiento'),
        ('confirmed', 'Orden de Trabajo'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True, copy=False)

    assembly_length = fields.Float(string='Longitud entre centros')
    barrel_length = fields.Float(string='Longitud de la camisa')
    piston_width = fields.Float(string='Ancho del pistón')
    head_width = fields.Float(string='Ancho de la cabeza')
    head_diameter = fields.Float(string='Diámetro de la cabeza')
    rod_length = fields.Float(string='Longitud del vástago')

    def action_confirm(self):
        """Pasa de Levantamiento a Orden de Trabajo"""
        for record in self:
            if not record.operational_record_ids:
                raise ValidationError("No puedes confirmar una Orden de Trabajo sin líneas de registro operativo.")
            record.state = 'confirmed'

    def action_set_draft(self):
        """Permite regresar a borrador si es necesario"""
        self.write({'state': 'draft'})

    def action_cancel(self):
        """Cancela el registro"""
        self.write({'state': 'cancel'})

    @api.depends('operational_record_ids.hr', 'operational_record_ids.work_to_do')
    def _compute_operational_totals(self):
        for record in self:
            # Cantidad de registros y suma de horas
            lines = record.operational_record_ids
            record.total_tasks = len(lines)
            record.total_hours = sum(line.hr for line in lines)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("impsa.cylinder.survey")
                    or "Nuevo"
                )

        return super(CylinderSurvey, self).create(vals_list)
