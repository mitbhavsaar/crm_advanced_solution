# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class CrmMaterialLine(models.Model):
    _inherit = "crm.material.line"

    product_config_mode = fields.Selection(
        related='product_template_id.product_config_mode',
        depends=['product_template_id'],
        help="Product configuration mode"
    )

    product_custom_attribute_value_ids = fields.One2many(
        comodel_name='product.attribute.custom.value',
        inverse_name='crm_order_line_id',
        string="Custom Values",
        compute='_compute_custom_attribute_values',
        help="Product custom attribute values",
        store=True,
        readonly=False,
        precompute=True,
        copy=True
    )
    
    attributes_description = fields.Text(
        string=" Description",
        compute="_compute_attributes_description",
        store=True
    )

    attributes_json = fields.Json(
        string="Attribute Map",
        compute="_compute_attributes_json",
        store=True
    )
    
    
    @api.depends(
        'product_template_attribute_value_ids',
        'product_custom_attribute_value_ids',
        'attached_file_name'
    )
    def _compute_attributes_description(self):
        """Attributes description WITHOUT file upload"""
        for record in self:
            template_attrs = []

            for ptav in record.product_template_attribute_value_ids:
                attr = ptav.attribute_id
                if not attr:
                    continue

                display_type = attr.display_type
                key = attr.name

                # 🔥 SKIP file_upload completely
                if display_type == "file_upload":
                    continue

                # M2O
                if display_type == "m2o" and ptav.m2o_res_id:
                    model = attr.m2o_model_id.model
                    rec = self.env[model].sudo().browse(ptav.m2o_res_id)
                    value = rec.display_name
                else:
                    value = ptav.name

                if value:
                    template_attrs.append(f"{key}: {value}")

            # Custom Attributes
            custom_attrs = []
            for custom in record.product_custom_attribute_value_ids:
                ptav = custom.custom_product_template_attribute_value_id
                if ptav and ptav.attribute_id:
                    custom_attrs.append(f"{ptav.attribute_id.name}: {custom.custom_value}")

            # Final result (NO FILE)
            record.attributes_description = ", ".join(template_attrs + custom_attrs) if (template_attrs or custom_attrs) else ""

            
    @api.depends(
        'attached_file_id',
        'attached_file_name',
        'product_template_attribute_value_ids',
        'product_custom_attribute_value_ids',
    )
    def _compute_attributes_json(self):
        """Attributes JSON WITHOUT file upload"""
        for record in self:
            data = {}
            
            try:
                # Template attributes (SKIP file_upload)
                for ptav in record.product_template_attribute_value_ids:
                    attr = ptav.attribute_id
                    if not attr or getattr(ptav, 'is_custom', False):
                        continue

                    key = attr.name
                    display_type = attr.display_type

                    # 🔥 SKIP file_upload from JSON
                    if display_type == "file_upload":
                        continue

                    # M2O
                    if display_type == "m2o" and ptav.m2o_res_id:
                        rec = self.env[attr.m2o_model_id.model].sudo().browse(ptav.m2o_res_id)
                        data[key] = rec.display_name
                        continue

                    # Normal
                    data[key] = ptav.name

                # Custom Attributes
                for custom in record.product_custom_attribute_value_ids:
                    ptav = custom.custom_product_template_attribute_value_id
                    if ptav and ptav.attribute_id:
                        data[ptav.attribute_id.name] = custom.custom_value

            except Exception as e:
                _logger.exception(f"❌ Error computing attributes_json: {e}")

            record.attributes_json = data
            _logger.debug(f"✅ attributes_json for Line {record.id}: {data}")

    @api.depends('product_id')
    def _compute_custom_attribute_values(self):
        """
        Checks if the product has custom attribute values associated with it,
        and if those values belong to the valid values of the product template.
        """
        for line in self:
            if not line.product_id:
                line.product_custom_attribute_value_ids = False
                continue
            if not line.product_custom_attribute_value_ids:
                continue
            valid_values = line.product_id.product_tmpl_id. \
                valid_product_template_attribute_line_ids. \
                product_template_value_ids
            # Remove the is_custom values that don't belong to this template
            for attribute in line.product_custom_attribute_value_ids:
                if attribute.custom_product_template_attribute_value_id not in valid_values:
                    line.product_custom_attribute_value_ids -= attribute
    
    @api.model
    def get_list_data(self, list_id, field_names):
        """
        Override to provide data including dynamic attributes from attributes_json
        """
        _logger.info(f"🟢 get_list_data called: list_id={list_id}, fields={field_names}")
        
        try:
            line_id = int(list_id)
        except (ValueError, TypeError):
            _logger.error("Invalid list_id: %s", list_id)
            return []

        line = self.browse(line_id)
        if not line.exists():
            _logger.warning("Line %s not found", line_id)
            return []

        row = {"id": line.id}

        for field in field_names:
            if field in self._fields:
                # Standard field
                val = line[field]
                if hasattr(val, "display_name"):
                    row[field] = val.display_name
                else:
                    row[field] = val
                _logger.info(f"✅ Standard field '{field}' = '{row[field]}'")
            else:
                # Dynamic attribute from attributes_json
                attrs = line.attributes_json or {}
                row[field] = attrs.get(field, "")
                _logger.info(f"🔵 Dynamic field '{field}' = '{row[field]}' from attributes_json")

        _logger.info(f"🟢 Final row data: {row}")
        return [row]