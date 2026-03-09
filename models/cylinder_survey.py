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

    cylinder_qty = fields.Integer(
        string="Cantidad", 
        default=1, 
        required=True, 
        tracking=True,
        help="Número de cilindros que comparten exactamente estas mismas características."
    )

    image_ids = fields.One2many(
        'impsa.cylinder.image', 
        'survey_id', 
        string="Galería de Imágenes"
    )

    # Camisa (Sleeve/Barrel)
    diameter_sleeve = fields.Float(string="Ø Camisa")
    barrel_length = fields.Float(string='Largo de Camisa')
    sleeve_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes de la Camisa", 
        domain=[('component', '=', 'sleeve')]
    )

    # Vástago (Rod)
    diameter_rod = fields.Float(string="Ø Vástago")
    rod_length = fields.Float(string='Largo de Vástago')
    rod_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes del Vástago", 
        domain=[('component', '=', 'rod')]
    )

    # Émbolo (Piston)
    piston_diameter = fields.Float(string='Ø Émbolo') 
    piston_width = fields.Float(string='Ancho de Émbolo')
    piston_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes del Émbolo", 
        domain=[('component', '=', 'piston')]
    )

    # Cabeza (Head)
    head_diameter = fields.Float(string='Ø Cabeza')
    head_width = fields.Float(string='Ancho de Cabeza')
    head_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes de la Cabeza", 
        domain=[('component', '=', 'head')]
    )

    # General / Carrera
    stroke = fields.Float(string="Carrera")
    assembly_length = fields.Float(string='Largo Ensamble (Centro a Centro)')
    assembly_image_ids = fields.One2many(
        'impsa.cylinder.image', 'survey_id', 
        string="Imágenes del Ensamble", 
        domain=[('component', '=', 'assembly')]
    )

    date = fields.Date(string="Fecha", default=fields.Date.context_today)
    description = fields.Char(string="Descripción")
    cylinder_type = fields.Char(string="Cilindro de")
    identification_marks = fields.Char(
        string="Identificación", 
        help="Marcas, características o notas visuales para identificar el cilindro físicamente.",
        tracking=True
    )

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

    # Restricción de seguridad para evitar errores de captura
    @api.constrains('cylinder_qty')
    def _check_cylinder_qty(self):
        for record in self:
            if record.cylinder_qty <= 0:
                raise ValidationError("La cantidad de cilindros a evaluar debe ser al menos 1.")

    def action_confirm(self):
        """Pasa de Levantamiento a Orden de Trabajo y actualiza la referencia"""
        for record in self:
            if not record.operational_record_ids:
                raise ValidationError("No puedes confirmar una Orden de Trabajo sin líneas de registro operativo.")
            
            # Cambiar prefijo para indicar que ya es una Orden de Trabajo
            new_name = record.name
            if new_name and new_name.startswith('LEV-'):
                new_name = new_name.replace('LEV-', 'OT-', 1)
                
            record.write({
                'state': 'confirmed',
                'name': new_name
            })

    def action_set_draft(self):
        """Permite regresar a borrador y restaura el prefijo original"""
        for record in self:
            new_name = record.name
            if new_name and new_name.startswith('OT-'):
                new_name = new_name.replace('OT-', 'LEV-', 1)
                
            record.write({
                'state': 'draft',
                'name': new_name
            })

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
