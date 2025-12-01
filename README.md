CRM Advanced Solution – Functional Documentation
  Overview

The CRM Advanced Solution bundle enhances Odoo CRM with usability, product configuration, and spreadsheet automation features.
It is divided into three sub-modules:

crm_customisation – Improves CRM lead/contact experience
crm_product_configurator – Adds a powerful attribute-based product configurator in CRM
crm_spreadsheet_enhancement – Integrates CRM with spreadsheet-based cost calculators, similar to Sales Quotes

1 crm_customisation

🔹 Purpose
To improve contact management and CRM usability by enhancing views, auto-addressing, and parent–child contact handling.
  Key Features
  
- Default List View
CRM now opens directly in List View instead of Kanban
Only Parent Partner Name is shown (child contacts are excluded for readability)

- Additional Contacts Tab
A new tab “Additional Contacts” is added to the CRM Lead form
Displays all child contacts linked to the selected parent customer
Updates reflect automatically in real time when child contacts are added, modified, or deleted

- Contact Form Enhancements
Auto-Fill City and State based on Pincode
When entering a pincode, the system automatically fetches City and State
Increases accuracy and reduces manual entry effort

2 crm_product_configurator

🔹 Purpose
To configure dynamic product variants, attributes, pricing, and file-based inputs directly from CRM.
Key Features

- Product Tab + Material Lines
A new Product tab is added inside CRM Leads
Includes crm.material.line (One2Many) to manage line-wise product selections

- Variant-Based Configurator Popup
When a selected product has variants, a Configurator Popup opens
Users can:
Enter Quantity
Get dynamic Pricing
View every attribute
Select Attribute Values

- Advanced Attribute Display Types
Display Type	Functionality
File Upload	Upload, replace, or remove files as attribute values. Stored separately and downloadable later.
Many2One Selector (M2O)	Select any Odoo model → list records → choose record as attribute value.

- Data Finalization on Confirm
When the configurator is confirmed:
Attribute values merge into the line description
File uploads stored on the product line
Quantity, Price & Attributes fully applied to the CRM line

3 crm_spreadsheet_enhancement

🔹 Purpose
To provide automated spreadsheet cost calculators for CRM leads, similar to Sales Quote Calculator.

  Key Features
- Enable / Disable Setting
CRM spreadsheet calculator can be enabled from Settings → CRM

- Template Selection
New field added in settings: Quote Calculator Template
Selected template is used while generating CRM calculators

- Smart Button in CRM Lead
A Cost Calculator smart button appears on the CRM Lead
Creates individual sheets for every CRM material line

- Sheet Auto-Generation
Each generated sheet includes:
Header	Source
Product	CRM Material Line Product
Quantity	Material Line Quantity
Others	Extracted dynamically from line description

- Sync & Save Workflow
Sync with Fields → Updates spreadsheet automatically based on CRM line values
Save → Applies the sheet values back to CRM in bulk

 Result

The CRM Advanced Solution enables:
Better CRM handling and data accuracy
Strong product configuration directly inside CRM
Automated spreadsheet-based cost estimation with real-time sync
