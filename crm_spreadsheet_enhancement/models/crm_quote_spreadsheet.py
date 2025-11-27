# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import json
import logging

_logger = logging.getLogger(__name__)

CRM_MATERIAL_LINE_BASE_FIELDS = [
    'product_template_id',
    'quantity',
]

class CrmLeadSpreadsheet(models.Model):
    _name = 'crm.lead.spreadsheet'
    _inherit = 'spreadsheet.mixin'
    _description = 'CRM Quotation Spreadsheet'

    name = fields.Char(required=True)
    lead_id = fields.Many2one('crm.lead', string="Opportunity", ondelete='cascade')
    sale_id = fields.Many2one('sale.order', string="Sale Order", ondelete='set null')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    raw_spreadsheet_data = fields.Text("Raw Spreadsheet Data")

    # ------------------------------------------------------------------
    # ✅ CRITICAL: Override get_list_data (PUBLIC METHOD)
    # ------------------------------------------------------------------
    @api.model
    def get_list_data(self, model, list_id, field_names):
        """
        ✅ THIS IS CALLED BY SPREADSHEET JS
        Override base spreadsheet method to handle dynamic attributes
        """
        _logger.info(f"🟡 [Spreadsheet] get_list_data called: model={model}, list_id={list_id}, fields={field_names}")
        
        if model != 'crm.material.line':
            _logger.info(f"⚪ Not CRM model, using super: {model}")
            return super().get_list_data(model, list_id, field_names)
        
        try:
            line_id = int(list_id)
        except (ValueError, TypeError):
            _logger.error(f"❌ Invalid list_id: {list_id}")
            return []

        line = self.env['crm.material.line'].browse(line_id)
        if not line.exists():
            _logger.warning(f"❌ Material line {line_id} not found")
            return []

        _logger.info(f"✅ Found line {line_id}: {line.product_template_id.display_name}")
        
        # Get attributes_json FIRST
        attrs = line.attributes_json or {}
        _logger.info(f"📦 attributes_json: {attrs}")

        row = {"id": line.id}

        for field in field_names:
            if field in line._fields:
                # Standard Odoo field
                val = line[field]
                if hasattr(val, "display_name"):
                    row[field] = val.display_name
                else:
                    row[field] = val
                _logger.info(f"✅ Standard field '{field}' = '{row[field]}'")
            else:
                # Dynamic attribute from attributes_json
                row[field] = attrs.get(field, "")
                _logger.info(f"🔵 Dynamic field '{field}' = '{row[field]}'")

        _logger.info(f"🟡 Final row data: {row}")
        return [row]

    # ------------------------------------------------------------------
    # ✅ INTERNAL: _get_list_data (PRIVATE METHOD)
    # ------------------------------------------------------------------
    def _get_list_data(self, list_id):
        """
        Internal method for other operations
        """
        self.ensure_one()
        
        try:
            list_id_int = int(list_id)
        except (ValueError, TypeError):
            return []

        line = self.env['crm.material.line'].browse(list_id_int)
        if not line.exists():
            return []

        row = {
            'id': line.id,
            'product_template_id': line.product_template_id.display_name if line.product_template_id else '',
            'quantity': line.quantity or 0,
        }

        attrs = line.attributes_json or {}
        for key, value in attrs.items():
            row[key] = value

        return [row]

    # ------------------------------------------------------------------
    # OPEN FORMVIEW
    # ------------------------------------------------------------------
    def get_formview_action(self, access_uid=None):
        return self.action_open_spreadsheet()

    def action_open_spreadsheet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'action_crm_lead_spreadsheet',
            'params': {
                'spreadsheet_id': self.id,
                'model': 'crm.lead.spreadsheet',
            },
        }

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.lead_id and rec.lead_id.material_line_ids:
                for line in rec.lead_id.material_line_ids:
                    rec.with_context(material_line_id=line.id)._dispatch_insert_list_revision()
        return records

    # ------------------------------------------------------------------
    # JOIN SESSION
    # ------------------------------------------------------------------
    def join_spreadsheet_session(self, access_token=None):
        self.ensure_one()

        self._sync_sheets_with_material_lines()

        data = super().join_spreadsheet_session(access_token)
        data.update({
            'lead_id': self.lead_id.id if self.lead_id else False,
            'lead_display_name': self.lead_id.display_name if self.lead_id else False,
            'sheet_id': self.id
        })

        spreadsheet_json = data.get('data') or {}
        lists = spreadsheet_json.get('lists') or {}
        sheets = spreadsheet_json.get('sheets') or []

        current_line_ids = set(self.lead_id.material_line_ids.ids) if self.lead_id else set()
        existing_list_ids = {int(list_id) for list_id in lists.keys() if list_id.isdigit()}

        missing_ids = current_line_ids - existing_list_ids
        removed_ids = existing_list_ids - current_line_ids

        # Add sheets
        for line_id in missing_ids:
            new_sheet = self._create_sheet_for_material_line(line_id)
            lists[str(line_id)] = new_sheet['list']
            sheets.append(new_sheet['sheet'])

        # Remove sheets
        if removed_ids:
            for rid in removed_ids:
                if str(rid) in lists:
                    del lists[str(rid)]
            sheets = [s for s in sheets if not any(str(rid) in json.dumps(s) for rid in removed_ids)]

        spreadsheet_json['lists'] = lists
        spreadsheet_json['sheets'] = sheets
        
        # ✅ CRITICAL FIX: Preload data for ALL lists
        _logger.info("🔥 Preloading data for all lists...")
        for list_id, list_config in lists.items():
            try:
                line_id = int(list_id)
                line = self.env['crm.material.line'].browse(line_id)
                if line.exists():
                    columns = list_config.get('columns', [])
                    list_data = self.get_list_data('crm.material.line', list_id, columns)
                    _logger.info(f"✅ Preloaded list {list_id}: {list_data}")
            except Exception as e:
                _logger.error(f"❌ Failed to preload list {list_id}: {e}")
        
        data['data'] = spreadsheet_json
        self.raw_spreadsheet_data = json.dumps(spreadsheet_json)

        return data

    # ------------------------------------------------------------------
    # EMPTY DATA (initial load)
    # ------------------------------------------------------------------
    def _empty_spreadsheet_data(self):
        data = super()._empty_spreadsheet_data() or {}
        data.setdefault('lists', {})
        data['sheets'] = []

        if not self.lead_id or not self.lead_id.material_line_ids:
            return data

        for line in self.lead_id.material_line_ids:
            sheet_id = f"sheet_{line.id}"
            list_id = str(line.id)
            product_name = (line.product_template_id.display_name or "Item")[:31]

            # dynamic attributes
            dynamic_keys = list(line.attributes_json.keys()) if isinstance(line.attributes_json, dict) else []
            columns = CRM_MATERIAL_LINE_BASE_FIELDS + dynamic_keys

            data['sheets'].append({'id': sheet_id, 'name': product_name})

            data['lists'][list_id] = {
                'id': list_id,
                'model': 'crm.material.line',
                'columns': columns,
                'domain': [['id', '=', line.id]],
                'sheetId': sheet_id,
                'name': product_name,
                'context': {},
                'orderBy': [],
                'fieldMatching': {
                    'material_line_ids': {'chain': 'lead_id', 'type': 'many2one'},
                },
            }

        return data

    # ------------------------------------------------------------------
    # INSERT REVISION (create new sheet on new line)
    # ------------------------------------------------------------------
    def _dispatch_insert_list_revision(self):
        self.ensure_one()

        line_id = self._context.get('material_line_id')
        if not line_id:
            return

        line = self.env['crm.material.line'].browse(line_id)
        if not line.exists():
            return

        sheet_id = f"sheet_{line.id}"
        list_id = str(line.id)
        product_name = (line.product_template_id.display_name or "Item")[:31]

        # Get dynamic keys and all columns
        dynamic_keys = list(line.attributes_json.keys()) if isinstance(line.attributes_json, dict) else []
        columns = CRM_MATERIAL_LINE_BASE_FIELDS + dynamic_keys

        _logger.info(f"🔧 Creating sheet for line {line_id} with columns: {columns}")

        # ✅ Build column metadata with proper types
        columns_meta = []
        for col in columns:
            if col in self.env['crm.material.line']._fields:
                ftype = self.env['crm.material.line']._fields[col].type
            else:
                # Dynamic attribute - treat as char
                ftype = 'char'
            columns_meta.append({'name': col, 'type': ftype})

        # ✅ CRITICAL FIX: Get actual data NOW
        attrs = line.attributes_json or {}
        _logger.info(f"📦 Line {line_id} attributes_json: {attrs}")

        # Build the actual row data that will be inserted
        row_data = []
        for col_meta in columns_meta:
            field_name = col_meta['name']
            
            if field_name in line._fields:
                # Standard field
                val = line[field_name]
                if hasattr(val, 'display_name'):
                    cell_value = val.display_name
                else:
                    cell_value = val if val is not False else ''
            else:
                # Dynamic attribute
                cell_value = attrs.get(field_name, '')
            
            row_data.append(cell_value)
            _logger.info(f"  📝 {field_name} = {cell_value}")

        commands = [
            {'type': 'CREATE_SHEET', 'sheetId': sheet_id, 'name': product_name},
            {
                'type': 'REGISTER_ODOO_LIST',
                'listId': list_id,
                'model': 'crm.material.line',
                'columns': columns,
                'domain': [['id', '=', line.id]],
                'context': {},
                'orderBy': [],
            },
            {
                'type': 'RE_INSERT_ODOO_LIST',
                'sheetId': sheet_id,
                'col': 0,
                'row': 0,
                'id': list_id,
                'linesNumber': 1,
                'columns': columns_meta,
            },
        ]

        # ✅ CRITICAL: Insert actual cell values immediately after creating the list
        for col_idx, (col_meta, cell_value) in enumerate(zip(columns_meta, row_data)):
            commands.append({
                'type': 'UPDATE_CELL',
                'sheetId': sheet_id,
                'col': col_idx,
                'row': 1,  # Row 1 is data row (Row 0 is header)
                'content': str(cell_value) if cell_value not in (None, False, '') else '',
            })

        # Add table formatting
        commands.append({
            'type': 'CREATE_TABLE',
            'sheetId': sheet_id,
            'tableType': 'static',
            'ranges': [{
                '_sheetId': sheet_id,
                '_zone': {'top': 0, 'bottom': 1, 'left': 0, 'right': len(columns_meta) - 1}
            }],
            'config': {
                'firstColumn': False,
                'hasFilters': True,
                'totalRow': False,
                'bandedRows': True,
                'styleId': 'TableStyleMedium5',
            }
        })

        # Final update command
        commands.append({'type': 'UPDATE_ODOO_LIST_DATA', 'listId': list_id})

        _logger.info(f"📤 Dispatching {len(commands)} commands for sheet {sheet_id}")
        self._dispatch_commands(commands)

    # ------------------------------------------------------------------
    # SYNC WITH MATERIAL LINES
    # ------------------------------------------------------------------
    def _sync_sheets_with_material_lines(self):
        self.ensure_one()
        if not self.lead_id:
            return

        data = json.loads(self.raw_spreadsheet_data) if self.raw_spreadsheet_data else {}
        current_sheets = data.get('sheets', [])
        current_lists = data.get('lists', {})
        current_line_ids = set(self.lead_id.material_line_ids.ids)

        # Remove deleted
        for sheet in current_sheets:
            sid = sheet.get('id')
            if sid and sid.startswith("sheet_"):
                try:
                    line_id = int(sid.replace("sheet_", ""))
                    if line_id not in current_line_ids:
                        self._delete_sheet_for_material_line(line_id)
                except:
                    pass

        # Re-add missing
        existing_sheet_ids = {int(s['id'].replace('sheet_', '')) for s in current_sheets if s.get('id', '').startswith('sheet_')}
        for line in self.lead_id.material_line_ids:
            if line.id not in existing_sheet_ids:
                self.with_context(material_line_id=line.id)._dispatch_insert_list_revision()

    # ------------------------------------------------------------------
    # CREATE SHEET STRUCTURE
    # ------------------------------------------------------------------
    def _create_sheet_for_material_line(self, material_line_id):
        self.ensure_one()

        line = self.env['crm.material.line'].browse(material_line_id)
        if not line.exists():
            return {'sheet': {}, 'list': {}}

        sheet_id = f"sheet_{line.id}"
        list_id = str(line.id)
        name = (line.product_template_id.display_name or "Item")[:31]

        dynamic_keys = list(line.attributes_json.keys()) if isinstance(line.attributes_json, dict) else []
        columns = CRM_MATERIAL_LINE_BASE_FIELDS + dynamic_keys

        return {
            'sheet': {'id': sheet_id, 'name': name},
            'list': {
                'id': list_id,
                'model': 'crm.material.line',
                'columns': columns,
                'domain': [['id', '=', line.id]],
                'sheetId': sheet_id,
                'name': name,
                'context': {},
                'orderBy': [],
                'fieldMatching': {'material_line_ids': {'chain': 'lead_id', 'type': 'many2one'}},
            }
        }

    # ------------------------------------------------------------------
    # DELETE SHEET
    # ------------------------------------------------------------------
    def _delete_sheet_for_material_line(self, material_line_id):
        sheet_id = f"sheet_{material_line_id}"
        list_id = str(material_line_id)

        commands = [
            {'type': 'DELETE_SHEET', 'sheetId': sheet_id},
            {'type': 'UNREGISTER_ODOO_LIST', 'listId': list_id},
        ]

        try:
            self._dispatch_commands(commands)
        except:
            self._cleanup_deleted_sheets_from_data(material_line_id)

    def _cleanup_deleted_sheets_from_data(self, material_line_id):
        if not self.raw_spreadsheet_data:
            return
        try:
            data = json.loads(self.raw_spreadsheet_data)
            sid = f"sheet_{material_line_id}"
            if 'sheets' in data:
                data['sheets'] = [s for s in data['sheets'] if s.get('id') != sid]
            if 'lists' in data and str(material_line_id) in data['lists']:
                del data['lists'][str(material_line_id)]
            self.raw_spreadsheet_data = json.dumps(data)
        except:
            pass

    # ------------------------------------------------------------------
    # MANUAL SYNC BUTTON
    # ------------------------------------------------------------------
    def action_sync_sheets(self):
        for spreadsheet in self:
            spreadsheet._sync_sheets_with_material_lines()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _('Sheets synced with CRM Material Lines'),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    # ------------------------------------------------------------------
    # SPREADSHEET SELECTOR
    # ------------------------------------------------------------------
    @api.model
    def _get_spreadsheet_selector(self):
        return {
            'model': self._name,
            'display_name': _("CRM Quote Spreadsheets"),
            'sequence': 20,
            'allow_create': False,
        }

    # ------------------------------------------------------------------
    # DATA PROVIDER — used by spreadsheets
    # ------------------------------------------------------------------
    @api.model
    def get_crm_material_lines(self):
        self.ensure_one()
        if not self.lead_id:
            return []

        rows = []
        for line in self.lead_id.material_line_ids:

            row = {
                'id': line.id,
                'name': line.product_template_id.display_name if line.product_template_id else '',
                'quantity': line.quantity,
            }

            # Add dynamic JSON attributes
            attrs = line.attributes_json or {}
            for k, v in attrs.items():
                row[k] = v

            rows.append(row)

        return rows

    def getMainCrmMaterialLineLists(self):
        self.ensure_one()
        if not self.lead_id or not self.lead_id.material_line_ids:
            return []

        lists = []
        for line in self.lead_id.material_line_ids:

            dynamic_keys = list(line.attributes_json.keys()) if isinstance(line.attributes_json, dict) else []
            columns = CRM_MATERIAL_LINE_BASE_FIELDS + dynamic_keys

            lists.append({
                'id': str(line.id),
                'model': 'crm.material.line',
                'field_names': columns,
                'columns': columns,
                'name': line.product_template_id.display_name or f"Item {line.id}",
                'sheetId': f"sheet_{line.id}",
            })

        return lists