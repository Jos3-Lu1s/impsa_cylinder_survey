# from odoo import http


# class ImpsaCylinderSurvey(http.Controller):
#     @http.route('/impsa_cylinder_survey/impsa_cylinder_survey', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/impsa_cylinder_survey/impsa_cylinder_survey/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('impsa_cylinder_survey.listing', {
#             'root': '/impsa_cylinder_survey/impsa_cylinder_survey',
#             'objects': http.request.env['impsa_cylinder_survey.impsa_cylinder_survey'].search([]),
#         })

#     @http.route('/impsa_cylinder_survey/impsa_cylinder_survey/objects/<model("impsa_cylinder_survey.impsa_cylinder_survey"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('impsa_cylinder_survey.object', {
#             'object': obj
#         })

