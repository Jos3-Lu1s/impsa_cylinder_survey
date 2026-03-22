from odoo import models, fields, api

class CylinderImage(models.Model):
    _name = 'impsa.cylinder.image'
    _description = 'Imágenes del Cilindro'
    _order = 'sequence, id desc'

    survey_id = fields.Many2one(
        'impsa.cylinder.survey', 
        string='Levantamiento', 
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string="Secuencia", default=10)
    name = fields.Char(string="Descripción")
    
    # Categorizar la foto para saber de qué pieza es
    component = fields.Selection([
        ('barrel', 'Camisa'),
        ('rod', 'Vástago'),
        ('piston', 'Émbolo / Pistón'),
        ('head', 'Cabeza'),
        ('stroke', 'Carrera'),
        ('accessory', 'Accesorio'),
    ], string="Componente", required=True)

    # max_width y max_height para proteger el servidor de fotos de 10MB
    image = fields.Image(string="Imagen", max_width=1920, max_height=1920, required=True)

    @api.model_create_multi
    def create(self, vals_list):
        count_tracker = {}

        for vals in vals_list:
            if not vals.get('name'):
                comp = vals.get('component', 'misc')
                survey = vals.get('survey_id', False)
                
                # llave única para rastrear por levantamiento y componente
                tracker_key = (survey, comp)
                
                # Si es la primera vez que vemos esta combinación en este lote, buscamos en BD cuántos hay
                if tracker_key not in count_tracker:
                    existing_count = self.search_count([
                        ('survey_id', '=', survey),
                        ('component', '=', comp)
                    ])
                    count_tracker[tracker_key] = existing_count
                
                # Incrementamos el contador para esta foto
                count_tracker[tracker_key] += 1
                current_number = count_tracker[tracker_key]
                
                # Formato: IMG-COMPONENTE-NUMERO (ej. IMG-BARREL-1)
                comp_upper = comp.upper()
                vals['name'] = f"IMG-{comp_upper}-{current_number}"

        return super(CylinderImage, self).create(vals_list)