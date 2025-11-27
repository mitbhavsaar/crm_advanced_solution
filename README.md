##crm_advanced_solution

1. crm_customisation:

Overview

This module enhances Odoo CRM by improving views, contact handling, and overall usability. It modifies the default CRM workflow to provide a more user-friendly list view, parent–child contact management, and automatic address completion.

Key Features
1. Default List View (Instead of Kanban)

When CRM opens, the default view is now List View instead of Kanban.

The list shows the Partner Name (Parent only), excluding child contacts.

2. Additional Contacts Tab

A new tab called "Additional Contacts" is added on the CRM Lead form.

This tab automatically displays all child contacts linked to the selected parent customer.

If any child contact is updated or deleted, the changes reflect in this tab in real time.

3. Contact Form Enhancements

Auto-Fill Address Using Pincode

When the user enters a pincode, the system automatically fetches and fills:

City

State

This improves accuracy and speeds up address entry.

2. crm_product_configurator:

Overview

This module introduces an advanced product configurator inside CRM. When a product is selected on a CRM Lead, a full configurator opens to manage attributes, variants, quantity, pricing, and file-upload based attributes.

Key Features
1. Product Tab with Material Lines

The CRM Lead form includes a new Product tab.

It contains a crm.material.line One2Many table where product lines are created.

2. Variant-Based Configurator Popup

When the selected product has variants, a configurator popup opens.

Inside the configurator, the user can:

Adjust quantity

Fetch price automatically

View all attributes

Choose attribute values

3. Attribute Enhancements

Two new attribute display types have been introduced:

a) File Upload Display Type

If an attribute uses the File Upload display type:

User can upload a file as the attribute value

Can replace or remove the file

Uploaded file is stored in a separate field on the product line

After saving, the file is available for download by the user

b) M2O Selector Display Type

Display Type: Many2One Selector

User can select any Odoo model

All records of that model appear as a dropdown list

User can choose any record as the attribute value

4. On Confirm: Data Finalization

When the configurator is confirmed:

All attribute values are merged into the line description

Uploaded files are stored in a dedicated field

Price, Quantity, and Attributes are fully prepared on the CRM line

3. crm_spreadsheet_enhancement :

Overview

This module integrates CRM with Odoo Spreadsheet, similar to the Sales Quote Calculator.
It generates line-wise cost calculator sheets for each CRM lead automatically.

Key Features
1. Enable/Disable Setting

CRM spreadsheet calculator can be enabled/disabled from Settings → CRM.

Works the same as the Odoo Sales spreadsheet feature.

2. Template Selection

A new field “Quote Calculator Template” is added in CRM settings.

The selected template is used for generating CRM cost calculator sheets.

3. Smart Button in CRM Lead

A Cost Calculator smart button appears in the CRM Lead form.

Clicking it generates spreadsheet sheets for all material lines in the lead.

4. Automatic Sheet Generation

A separate sheet is created for every CRM material line.
Sheet headers include:

Field	Source
Product	Product from the CRM line
Quantity	Quantity from the material line
Other headers	Extracted from the line description
5. Sync with Fields

When the user clicks “Sync with fields”, the spreadsheet updates automatically with CRM line values.

Each sheet stays connected to its corresponding CRM line.

6. Bulk Update via Save

After modifying the spreadsheet, clicking Save updates all the sheets and applies the data line-wise back into CRM.

This workflow behaves exactly like the Sales Quote Calculator.
