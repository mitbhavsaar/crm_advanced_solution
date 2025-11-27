from odoo import models, fields

class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    display_type = fields.Selection(
        selection_add=[
            ('file_upload', 'File Upload'),
            ('m2o', 'Many2one Selector'),
        ],
        ondelete={
            'file_upload': 'set default',
            'm2o': 'set default',
        }
    )

    # NEW: Define which model will be used for the Many2one dropdown
    m2o_model_id = fields.Many2one(
        "ir.model",
        string="Many2one Model",
        help="Select the model whose records will be selectable as values."
    )
