{
    'name': "IMPSA: Levantamiento y Costeo de Cilindros",

    'summary': """
        Levantamiento técnico, Análisis de Precios Unitarios (APU), Cotizaciones y Suministros.
    """,

    'description': """
Gestión Integral de Taller de Cilindros (IMPSA)
==============================================

Módulo centralizado para el control de ingeniería y flujo comercial de cilindros. 
Optimiza la transición desde el levantamiento físico en taller hasta la generación de suministros y cotizaciones.

Características Principales:
---------------------------
* **Levantamiento Técnico (Survey):** Registro de dimensiones físicas, materiales, sellos y accesorios.
* **Ingeniería y Grupos:** Organización de cilindros por grupos técnicos para estandarización.
* **Análisis de Precios Unitarios (APU):** Motor de costeo detallado con márgenes configurables para materiales y mano de obra.
* **Integración Comercial:** Vinculación directa con CRM (Oportunidades) y Ventas (Sale Orders).
* **Gestión de Suministros:** Generación automática de Órdenes de Compra a proveedores basadas en los sellos detectados en el levantamiento.

Integración con procesos:
-------------------------
1. CRM -> Levantamiento -> APU -> Cotización -> Orden de Compra.
    """,

    'author': "Tekuno",
    'website': "https://tekuno.mx/",

    'category': 'Manufacturing/Operations',
    'version': '19.0.1.0.0',

<<<<<<< HEAD
    'depends': ['base', 'crm', 'mail', 'purchase', 'sale_crm', 'sale_management', 'sale_stock', 'mrp', 'hr',  #'approvals'
                ],
=======
    'depends': ['base', "crm", "mail", 'purchase', 'sale_crm', 'sale_management','mrp','hr'],
>>>>>>> 1a391fe80b61aba2c9b6270a7d8b0625aac85b09

    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        'data/cylinder_data.xml',
<<<<<<< HEAD
        #'data/approval_data.xml', 
        #'data/employee_data.xml',
          
=======
        
>>>>>>> 1a391fe80b61aba2c9b6270a7d8b0625aac85b09
        # 'data/paper_format.xml',
        'reports/report_actions.xml',
        # 'reports/cylinder_survey_report.xml',
        "data/paperformat.xml",
        "views/cylinder_survey_views.xml",
        "views/cylinder_options_views.xml",
        "views/cylinder_materials_views.xml",
        "views/accessory_type_views.xml",
        "views/crm_adition.xml",
        "views/purchase_views.xml",
<<<<<<< HEAD
        #"views/approval_request_views.xml",          
        "reports/report_proforma.xml",
        "reports/report_cut_order.xml",
=======
        "reports/report_proforma.xml",
>>>>>>> 1a391fe80b61aba2c9b6270a7d8b0625aac85b09
        "views/apu_survey_views.xml",
        "views/integration_menu.xml",
        "views/saler_view.xml",
        "views/hr_department_inherit_view.xml",
        "views/res_partner_inherit_view.xml",
        "views/apu_survey_actions_views.xml",
        "views/pricelist_access.xml",
        "views/apu_survey_passw_view.xml",
        "views/apu_survey_margins_views.xml",
        "views/crm_stage_change.xml",
        "views/res_partner_bank_views.xml",
    ],
    
<<<<<<< HEAD
   'assets': {
      'web.assets_backend': [
           'impsa_cylinder_survey/static/src/css/crm_hide_send.css',
=======
    'assets': {
        'web.assets_backend': [
            'impsa_cylinder_survey/static/src/css/crm_hide_send.css',
>>>>>>> 1a391fe80b61aba2c9b6270a7d8b0625aac85b09
        ],
    },

    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

