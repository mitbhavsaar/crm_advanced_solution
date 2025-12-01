/** @odoo-module */

import { Component } from "@odoo/owl";
import { formatCurrency } from "@web/core/currency";
import { onMounted } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

export class ProductTemplateAttributeLine extends Component {
    static template = "crmProductConfigurator.ptal";

    static props = {
        productTmplId: Number,
        id: Number,
        attribute: {
            type: Object,
            shape: {
                id: Number,
                name: String,
                display_type: {
                    type: String,
                    validate: t =>
                        [
                            "color",
                            "multi",
                            "pills",
                            "radio",
                            "select",
                            "file_upload",
                            "m2o",
                            "strictly_numeric"       // 🔥 NEW TYPE VALIDATION
                        ].includes(t),
                },
                m2o_model_id: { type: [Boolean, Object], optional: true },
                m2o_values: { type: Array, element: Object, optional: true },
                pair_with_previous: { type: Boolean, optional: true },
                is_width_check: { type: Boolean, optional: true }, // 🔥 NEW
                m2o_model_technical_name: { type: [String, Boolean], optional: true }, // 🔥 NEW

            },
        },
        attribute_values: {
            type: Array,
            element: {
                type: Object,
                shape: {
                    id: Number,
                    name: String,
                    html_color: [Boolean, String],
                    image: [Boolean, String],
                    is_custom: Boolean,
                    excluded: { type: Boolean, optional: true },
                    m2o_res_id: { optional: true },
                },
            },
        },
        selected_attribute_value_ids: { type: Array, element: Number },
        create_variant: {
            type: String,
            validate: t => ["always", "dynamic", "no_variant"].includes(t),
        },
        customValue: { type: [{ value: false }, String], optional: true },
        m2o_values: { type: Array, element: Object, optional: true },
    };

    setup() {
        this.fileState = { fileName: null, fileData: null };
        this.m2oSelectedId = null;
        this.numericWarning = "";

        onMounted(() => {
            if (
                this.props.attribute_values.length === 1 &&
                this.props.selected_attribute_value_ids.length === 0 &&
                this.props.attribute.display_type !== "m2o"
            ) {
                this.updateSelectedPTAV({
                    target: { value: this.props.attribute_values[0].id.toString() },
                });
            }

            if (this.props.attribute.display_type === "m2o") {
                this.m2oSelectedId = null;
                if (this.env.updateM2OValue) {
                    this.env.updateM2OValue(
                        this.props.productTmplId,
                        this.props.id,
                        null
                    );
                }
            }
        });
    }

    updateSelectedPTAV(event) {
        this.env.updateProductTemplateSelectedPTAV(
            this.props.productTmplId,
            this.props.id,
            event.target.value,
            this.props.attribute.display_type === "multi"
        );
    }

    updateCustomValue(event) {
        this.env.updatePTAVCustomValue(
            this.props.productTmplId,
            this.props.selected_attribute_value_ids[0],
            event.target.value
        );
    }

    getPTAVTemplate() {
        switch (this.props.attribute.display_type) {
            case "color":
                return "crmProductConfigurator.ptav-color";
            case "multi":
                return "crmProductConfigurator.ptav-multi";
            case "pills":
                return "crmProductConfigurator.ptav-pills";
            case "radio":
                return "crmProductConfigurator.ptav-radio";
            case "select":
                return "crmProductConfigurator.ptav-select";
            case "file_upload":
                return "entrivis_file_upload.ptav-file-upload";
            case "m2o":
                return "crmProductConfigurator.ptav-m2o";
            case "strictly_numeric":         // 🔥 NEW TEMPLATE CASE
                return "crmProductConfigurator.ptav-strictly-numeric";
        }
    }

    getPTAVSelectName(ptav) {
        return ptav.name;
    }

    isSelectedPTAVCustom() {
        return this.props.attribute_values.find(
            ptav => this.props.selected_attribute_value_ids.includes(ptav.id)
        )?.is_custom;
    }

    hasPTAVCustom() {
        return this.props.attribute_values.some(ptav => ptav.is_custom);
    }

    isSingleValueReadOnly() {
        return (
            this.props.attribute_values.length === 1 &&
            !this.hasPTAVCustom()
        );
    }

    getSelectedPTAV() {
        return this.props.attribute_values.find(v =>
            this.props.selected_attribute_value_ids.includes(v.id)
        );
    }

    getFileName() {
        return this.fileState.fileName || "";
    }

    async uploadFile(ev) {
        const file = ev.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async e => {
            const base64 = e.target.result.split(",")[1];
            this.fileState.fileName = file.name;
            this.fileState.fileData = base64;

            if (this.env.updateFileUpload) {
                this.env.updateFileUpload(
                    this.props.productTmplId,
                    this.props.id,
                    { file_name: file.name, file_data: base64 }
                );
            }
            this.render();
        };
        reader.readAsDataURL(file);
    }

    removeUploadedFile() {
        this.fileState.fileName = null;
        this.fileState.fileData = null;

        if (this.env.updateFileUpload) {
            this.env.updateFileUpload(
                this.props.productTmplId,
                this.props.id,
                null
            );
        }
        this.render();
    }
    validateNumeric(event) {
        const value = event.target.value;
        const isValid = /^[0-9]*$/.test(value);

        if (!isValid) {
            this.numericWarning = "Only numeric values are allowed";
        } else {
            this.numericWarning = "";
        }

        // restrict input visually
        event.target.value = value.replace(/[^0-9]/g, "");

        // save the cleaned numeric value
        this.updateCustomValue(event);
        this.render();
    }

    async updateSelectedM2O(ev) {
        const resId = parseInt(ev.target.value || 0);

        this.env.updateM2OValue(
            this.props.productTmplId,
            this.props.id,
            resId || null
        );

        if (!resId) {
            // Reset width if profile name is cleared
            if (this.props.attribute.m2o_model_technical_name === "profile.name" && this.env.autoFillWidthFromM2O) {
                this.env.autoFillWidthFromM2O(this.props.productTmplId, "");
                this.render();
            }
            return;
        }

        // only for profile width autofill
        if (
            this.props.attribute.m2o_model_technical_name === "profile.name"
        ) {
            console.log(`🔍 M2O selected for profile.name. ResID: ${resId}`);
            const result = await rpc("/web/dataset/call_kw/profile.name/read", {
                model: "profile.name",
                method: "read",
                args: [[resId], ["width"]],
                kwargs: {},
            });

            const width = result?.length ? result[0].width : "";
            console.log(`📏 Fetched width: ${width}`);

            if (this.env.autoFillWidthFromM2O) {
                this.env.autoFillWidthFromM2O(
                    this.props.productTmplId,
                    String(width)
                );
            } else {
                console.warn("❌ autoFillWidthFromM2O not found in env");
            }

            this.render();
        }
    }


    getSelectedM2OId() {
        return this.m2oSelectedId;
    }
}
