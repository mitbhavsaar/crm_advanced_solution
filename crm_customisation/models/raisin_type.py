from odoo import api, fields, models

class RaisinType(models.Model):
    _name = "raisin.type"
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    _description = "Raisin Type"

    name = fields.Char(string="Name", required=True)


class ProfileName(models.Model):
    _name = "profile.name"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Profile Name"

    name = fields.Char(string="Profile Name", required=True, tracking=True)
    width = fields.Float(string="Width", tracking=True)
    
class GelCoat(models.Model):
    _name = "gel.coat"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Gel Coat"

    name = fields.Char(string="Name", required=True, tracking=True)
