{
    'name': "Levantamiento de Cilindros IMPSA",

    'summary': "Formato digital F-05-01",

    'description': """
        Digitalización del formato F-05-01 para el levantamiento de cilindros hidráulicos.
        Permite capturar medidas de:
        - Camisa, Vástago, Pistón, Cabeza.
        - Trabajos a realizar (Cromado, sellos, etc.).
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Services/Field Service',
    'version': '19.0.1.0.0',

    'depends': ['base', "crm", "mail", 'purchase', 'sale_crm', 'sale_management','mrp','hr'],

    "data": [
        "security/ir.model.access.csv",
        'data/cylinder_data.xml',
        # 'data/paper_format.xml',
        'reports/report_actions.xml',
        # 'reports/cylinder_survey_report.xml',
        "data/ir_sequence_data.xml",
        "views/cylinder_survey_views.xml",
        "views/cylinder_options_views.xml",
        "views/cylinder_materials_views.xml",
        "views/accessory_type_views.xml",
        "views/crm_adition.xml",
        "views/saler_view.xml",
        "views/purchase_views.xml",
        "reports/report_proforma.xml",
        "views/apu_survey_views.xml",
        "views/integration_menu.xml",
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

