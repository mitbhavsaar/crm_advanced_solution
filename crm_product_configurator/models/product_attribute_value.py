from odoo import models, fields

class ProductAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    file_data = fields.Binary("Uploaded File")
    file_name = fields.Char("File Name")
    
        # NEW FIELD FOR M2O VALUE
    m2o_res_id = fields.Many2oneReference(
        string="Selected Record",
        model_field="attribute_id.m2o_model_id",
    )
