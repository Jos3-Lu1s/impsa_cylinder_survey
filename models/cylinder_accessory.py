from odoo import models, fields, api

class CylinderAccessoryType(models.Model):
    """Modelo de Catálogo gestionado por el Administrador"""
    _name = "impsa.accessory.type"
    _description = "Catálogo de Tipos de Accesorio"
    _order = "name"

    name = fields.Char(string="Accesorio", required=True)
    active = fields.Boolean(default=True)
    
    tech_template = fields.Text(
        string="Plantilla de Características",
        help="Plantilla que se autocompletará al seleccionar este accesorio. Ej: 'Ø Int: __, Ø Ext: __'"
    )

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'El nombre debe ser único',
    )

class CylinderSurveyAccessory(models.Model):
    """Líneas de accesorios dentro del levantamiento"""
    _name = "impsa.cylinder.accessory"
    _description = "Detalle de Accesorio en Levantamiento"

    survey_id = fields.Many2one(
        "impsa.cylinder.survey", 
        string="Levantamiento", 
        ondelete="cascade",
        required=True
    )
    
    accessory_type_id = fields.Many2one(
        "impsa.accessory.type", 
        string="Tipo de Accesorio", 
        required=True,
        ondelete="restrict"
    )
    
    quantity = fields.Integer(string="Cantidad", default=1, required=True)
    
    tech_details = fields.Text(
        string="Características / Medidas",
        help="Reemplaza los espacios de la plantilla con las medidas reales."
    )

    observations = fields.Text(string="Observaciones")

    # Automatización para inyectar la plantilla cuando elijen el tipo
    @api.onchange('accessory_type_id')
    def _onchange_accessory_type_id(self):
        for rec in self:
            if rec.accessory_type_id and rec.accessory_type_id.tech_template:
                # Solo sobreescribe si el campo está vacío, para no borrar trabajo previo del usuario
                if not rec.tech_details:
                    rec.tech_details = rec.accessory_type_id.tech_template