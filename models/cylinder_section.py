from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CylinderSection(models.Model):
    _name = 'impsa.cylinder.section'
    _description = 'Sección de Cilindro Telescópico'
    _order = 'sequence, id'

    survey_id = fields.Many2one(
        'impsa.cylinder.survey', 
        string='Levantamiento', 
        required=True, 
        ondelete='cascade'
    )
    
    sequence = fields.Integer(string="Secuencia", default=10)
    
    name = fields.Char(
        string="Descripción", 
        required=True,
        help="Ej: Camisa Principal, Primera Extensión, etc."
    )
    
    section_type = fields.Selection([
        ('main', 'Camisa Principal'),
        ('intermediate', 'Extensión Intermedia'),
        ('last', 'Última Extensión')
    ], string="Tipo de Sección", required=True)

    # ----------------------------------------------------
    # Dimensiones Generales
    # ----------------------------------------------------
    inner_diameter = fields.Float(
        string="Ø Interior", 
        required=True,
        help="Aplica para Camisa Principal y Extensiones Intermedias."
    )
    outer_diameter = fields.Float(
        string="Ø Exterior (Vástago)", 
        required=True,
        help="Todas las secciones tienen un diámetro exterior/vástago."
    )
    length = fields.Float(
        string="Longitud", 
        required=True,
        help="Todas las secciones tienen longitud."
    )

    # ----------------------------------------------------
    # Dimensiones del Émbolo
    # ----------------------------------------------------
    piston_diameter = fields.Float(
        string="Ø Émbolo", 
        required=True,
        help="No aplica en la camisa principal."
    )
    piston_length = fields.Float(
        required=True,
        string="Longitud de Émbolo"
    )

    # ----------------------------------------------------
    # Dimensiones de la Cabeza
    # ----------------------------------------------------
    head_diameter = fields.Float(
        string="Ø Cabeza", 
        required=True,
        help="No aplica en la última extensión."
    )
    head_length = fields.Float(
        required=True,
        string="Longitud de Cabeza"
    )
    
    has_apu = fields.Boolean(
        string='Tiene APU',
        compute='_compute_has_apu',
        store=False
    )
    
    @api.depends('survey_id', 'survey_id.has_apu')
    def _compute_has_apu(self):
        for sec in self:
            sec.has_apu = bool(sec.survey_id and sec.survey_id.sudo().has_apu)

    @api.constrains('inner_diameter', 'outer_diameter', 'length', 'piston_diameter', 'piston_length', 'head_diameter', 'head_length')
    def _check_strict_dimensions(self):
        """Asegura que los valores requeridos sean estrictamente mayores a 0 
        y los valores no requeridos se mantengan en 0."""
        for sec in self:
            errors = []
            
            # Reglas Generales (Aplica a todas las secciones)
            if sec.outer_diameter <= 0:
                errors.append("El Ø Exterior (Vástago) debe ser mayor a 0.")
            if sec.length <= 0:
                errors.append("La Longitud de la sección debe ser mayor a 0.")

            # Reglas por Tipo de Sección
            if sec.section_type == 'main':
                # Requeridos > 0 (Solo medidas de la camisa en sí)
                if sec.inner_diameter <= 0: 
                    errors.append("El Ø Interior debe ser mayor a 0.")
                if sec.head_diameter <= 0: 
                    errors.append("El Ø de Cabeza debe ser mayor a 0.")

                
                # Prohibidos: Ni Émbolo Ni Cabeza aplican en la Camisa Principal
                if sec.piston_diameter != 0 or sec.piston_length != 0:
                    errors.append("La camisa principal no lleva medidas de Émbolo (Deben ser 0).")
                """ if sec.head_diameter != 0 or sec.head_length != 0:
                    errors.append("La camisa principal no lleva medidas de Cabeza (Deben ser 0).") """
 
            elif sec.section_type == 'intermediate':
                # Requeridos > 0 (Todo aplica)
                if sec.inner_diameter <= 0: errors.append("El Ø Interior debe ser mayor a 0.")
                if sec.piston_diameter <= 0: errors.append("El Ø de Émbolo debe ser mayor a 0.")
                if sec.piston_length <= 0: errors.append("La Longitud de Émbolo debe ser mayor a 0.")
                if sec.head_diameter <= 0: errors.append("El Ø de Cabeza debe ser mayor a 0.")
                if sec.head_length <= 0: errors.append("La Longitud de Cabeza debe ser mayor a 0.")

            elif sec.section_type == 'last':
                # Requeridos > 0
                if sec.piston_diameter <= 0: errors.append("El Ø de Émbolo debe ser mayor a 0.")
                if sec.piston_length <= 0: errors.append("La Longitud de Émbolo debe ser mayor a 0.")
                
                # Prohibidos: No aplica Interior ni Cabeza
                #if sec.inner_diameter != 0: 
                #    errors.append("La última extensión es maciza, el Ø Interior debe ser 0.")
                if sec.head_diameter != 0 or sec.head_length != 0:
                    errors.append("La última extensión no lleva medidas de Cabeza (Deben ser 0).")

            if errors:
                raise ValidationError(_("Errores en '%(name)s':\n- %(errores)s") % {
                    'name': sec.name,
                    'errores': '\n- '.join(errors)
                })

    # ----------------------------------------------------
    # Onchange para limpiar datos basura en la UI
    # ----------------------------------------------------
    @api.onchange('section_type')
    def _onchange_section_type_clean_garbage(self):
        for sec in self:
            if sec.section_type == 'main':
                sec.piston_diameter = 0.0
                sec.piston_length = 0.0
                sec.head_diameter = 0.0
                sec.head_length = 0.0
            elif sec.section_type == 'last':
                sec.inner_diameter = 0.0
                sec.head_diameter = 0.0
                sec.head_length = 0.0